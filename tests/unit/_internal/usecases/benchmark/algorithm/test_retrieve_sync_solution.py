from unittest.mock import MagicMock

import pytest
from luna_quantum import Solution
from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench import MapperContainer  # type: ignore[attr-defined]
from luna_bench._internal.domain_models import AlgorithmResultDomain, JobStatus
from luna_bench._internal.usecases.benchmark import (
    AlgorithmRetrieveSyncSolutionsUcImpl,
)
from luna_bench._internal.usecases.benchmark.protocols import BackgroundRetrieveAlgorithmSyncUc
from luna_bench._internal.user_models import BenchmarkUserModel
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench.base_components import BaseAlgorithmSync
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.model_decoding_error import ModelDecodingError
from luna_bench.errors.run_errors.run_algorithm_runtime_error import RunAlgorithmRuntimeError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.fixtures.mock_database import SetupBenchmark

_solution = Solution._build(  # type: ignore[attr-defined]
    component_types=[],
    binary_cols=[],
    spin_cols=None,
    int_cols=None,
    real_cols=None,
    raw_energies=None,
    timing=None,
    counts=[],
)


class TestRetrieveSyncSolution:
    @classmethod
    def _configure_benchmark(
        cls,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> BenchmarkUserModel:
        benchmark_result = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark)
        assert is_successful(benchmark_result), "Failed to load benchmark"
        benchmark = benchmark_result.unwrap()
        assert benchmark.modelset is not None, "Failed to load modelset"

        fake_result_data = AlgorithmResultUserModel(
            meta_data=None,
            status=JobStatus.RUNNING,
            error=None,
            solution=None,
            task_id="an id",
            retrival_data=None,
            model_id=benchmark.modelset.models[0].id,
        )

        for m in setup_benchmark.modelset.models:
            for a in setup_benchmark.benchmark.algorithms:
                with setup_benchmark.transaction as t:
                    t.algorithm.set_result(
                        m.name, a.name, AlgorithmResultDomain.model_construct(**fake_result_data.model_dump())
                    )

        for b in benchmark.algorithms:
            b.results = {"default_model": fake_result_data.model_copy()}
        return benchmark

    @pytest.mark.parametrize(
        ("return_values", "exp"),
        [
            ([Nothing, Some(Success(_solution))], Success(None)),
            ([Nothing, Some(Failure(RuntimeError("an error")))], Failure("RuntimeError: an error")),
            (
                [Nothing, Some(Failure(RunAlgorithmRuntimeError(RuntimeError("an error"))))],
                Failure("RuntimeError: an error"),
            ),
        ],
    )
    def test_retrieve_sync_solution(
        self,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
        return_values: list[
            Maybe[
                Result[
                    Solution, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError
                ]
            ]
        ],
        exp: Result[None, str],
    ) -> None:
        benchmark = TestRetrieveSyncSolution._configure_benchmark(
            setup_benchmark=setup_benchmark,
            mapper=mapper,
        )
        mock_bg_retrieval = MagicMock(spec=BackgroundRetrieveAlgorithmSyncUc)
        mock_bg_retrieval.side_effect = return_values

        uc = AlgorithmRetrieveSyncSolutionsUcImpl(
            background_retrieve_sync=mock_bg_retrieval,
            transaction=setup_benchmark.transaction,
        )

        r: Result[None, ModelDecodingError | DataNotExistError | UnknownLunaBenchError | RunAlgorithmRuntimeError] = uc(
            benchmark=benchmark
        )

        assert is_successful(r)

        # Check user model set correct
        for a in benchmark.algorithms:
            if is_successful(exp):
                if isinstance(a.algorithm, BaseAlgorithmSync):
                    assert a.results["default_model"].solution is return_values[1].unwrap().unwrap()
                    assert a.results["default_model"].status is JobStatus.DONE
                else:
                    assert a.results["default_model"].solution is None
                    assert a.results["default_model"].status is JobStatus.RUNNING
            else:
                if isinstance(a.algorithm, BaseAlgorithmSync):
                    assert a.results["default_model"].status is JobStatus.FAILED
                    assert a.results["default_model"].error == exp.failure()
                else:
                    assert a.results["default_model"].solution is None
                    assert a.results["default_model"].status is JobStatus.RUNNING
