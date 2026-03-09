from typing import TYPE_CHECKING

from luna_model import Solution
from returns.pipeline import is_successful

from luna_bench import MapperContainer  # type: ignore[attr-defined]
from luna_bench._internal.domain_models import AlgorithmResultDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.usecases.benchmark import (
    AlgorithmRetrieveAsyncSolutionsUcImpl,
)
from luna_bench.base_components import BaseAlgorithmAsync
from luna_bench.entities import JobStatus
from luna_bench.entities.algorithm_result_entity import AlgorithmResultEntity
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from tests.unit.fixtures.mock_components import MockAsyncAlgorithm
from tests.unit.fixtures.mock_database import SetupBenchmark

if TYPE_CHECKING:
    from returns.result import Result

    from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
    from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
    from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError

_solution = Solution([])


class TestRetrieveAsyncSolution:
    @classmethod
    def _configure_benchmark(
        cls,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
        retrival_data: ArbitraryDataDomain | None,
    ) -> BenchmarkEntity:
        benchmark_result = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark)
        assert is_successful(benchmark_result), "Failed to load benchmark"
        benchmark = benchmark_result.unwrap()
        assert benchmark.modelset is not None, "Failed to load modelset"

        fake_result_data = AlgorithmResultEntity(
            meta_data=None,
            status=JobStatus.RUNNING,
            error=None,
            solution=None,
            task_id="an id",
            retrival_data=retrival_data,
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

    def test_retrieve_async_solution(
        self,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> None:
        benchmark = TestRetrieveAsyncSolution._configure_benchmark(
            setup_benchmark=setup_benchmark,
            mapper=mapper,
            retrival_data=ArbitraryDataDomain(),
        )

        uc = AlgorithmRetrieveAsyncSolutionsUcImpl(
            transaction=setup_benchmark.transaction,
        )

        r: Result[
            None, RunAlgorithmMissingError | RunModelsetMissingError | DataNotExistError | UnknownLunaBenchError
        ] = uc(benchmark=benchmark)

        assert is_successful(r)

        # Check user model set correct
        for a in benchmark.algorithms:
            if isinstance(a.algorithm, BaseAlgorithmAsync):
                solution = a.results["default_model"].solution
                fetch_result = MockAsyncAlgorithm().fetch_result(None, None)  # type: ignore[arg-type] # Using none for simplicity. The fake algorithm does nothing with this data anyway.
                assert solution is not None
                assert is_successful(fetch_result)
                assert solution == fetch_result.unwrap()
                assert a.results["default_model"].status is JobStatus.DONE
            else:
                assert a.results["default_model"].solution is None
                assert a.results["default_model"].status is JobStatus.RUNNING

    def test_missing_retrieval_data(
        self,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> None:
        benchmark = TestRetrieveAsyncSolution._configure_benchmark(
            setup_benchmark=setup_benchmark, mapper=mapper, retrival_data=None
        )

        uc = AlgorithmRetrieveAsyncSolutionsUcImpl(
            transaction=setup_benchmark.transaction,
        )

        r: Result[
            None, RunAlgorithmMissingError | RunModelsetMissingError | DataNotExistError | UnknownLunaBenchError
        ] = uc(benchmark=benchmark)

        assert is_successful(r)

        for a in benchmark.algorithms:
            if isinstance(a.algorithm, BaseAlgorithmAsync):
                assert a.results["default_model"].error is not None
                assert a.results["default_model"].status is JobStatus.FAILED
            else:
                assert a.results["default_model"].solution is None
                assert a.results["default_model"].status is JobStatus.RUNNING
