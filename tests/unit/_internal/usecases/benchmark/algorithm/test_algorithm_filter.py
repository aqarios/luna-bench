from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench.entities import JobStatus
from luna_bench.entities.algorithm_entity import AlgorithmEntity
from luna_bench.errors.run_errors.run_algorithm_missing_error import RunAlgorithmMissingError
from tests.unit.fixtures.mock_components import MockAlgorithm, MockAsyncAlgorithm

if TYPE_CHECKING:
    from luna_bench._internal.usecases.benchmark.protocols import AlgorithmFilterUc


class TestAlgorithmFilter:
    @pytest.mark.parametrize(
        ("algorithm_type", "algorithm", "exp"),
        [
            (
                AlgorithmType.ASYNC,
                None,
                Success(
                    [
                        AlgorithmEntity(
                            name="existing_async", status=JobStatus.CREATED, algorithm=MockAsyncAlgorithm(), results={}
                        )
                    ]
                ),
            ),
            (
                AlgorithmType.ASYNC,
                AlgorithmEntity(
                    name="existing_async", status=JobStatus.CREATED, algorithm=MockAsyncAlgorithm(), results={}
                ),
                Success(
                    [
                        AlgorithmEntity(
                            name="existing_async", status=JobStatus.CREATED, algorithm=MockAsyncAlgorithm(), results={}
                        )
                    ]
                ),
            ),
            (
                AlgorithmType.SYNC,
                None,
                Success(
                    [AlgorithmEntity(name="existing", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={})]
                ),
            ),
            (
                AlgorithmType.SYNC,
                AlgorithmEntity(name="existing", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={}),
                Success(
                    [AlgorithmEntity(name="existing", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={})]
                ),
            ),
            (
                AlgorithmType.ASYNC,
                AlgorithmEntity(name="existing", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={}),
                Success([]),
            ),
            (
                AlgorithmType.ASYNC,
                AlgorithmEntity(name="non_existing", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={}),
                Failure(RunAlgorithmMissingError("non_existing", "existing")),
            ),
        ],
    )
    def test_filter_by_algorithm_type(
        self,
        usecase: UsecaseContainer,
        algorithm_type: AlgorithmType,
        algorithm: AlgorithmEntity | None,
        exp: Result[list[AlgorithmEntity], RunAlgorithmMissingError],
    ) -> None:
        benchmark_result = usecase.benchmark_load_uc()(benchmark_name="existing")
        assert is_successful(benchmark_result), "Failed to load benchmark 'existing'"

        uc: AlgorithmFilterUc = usecase.benchmark_algorithm_filter_uc()

        result = uc(
            benchmark=benchmark_result.unwrap(),
            algorithm_type=algorithm_type,
            algorithm=algorithm,
        )
        assert is_successful(result) == is_successful(exp)

        if is_successful(exp):
            assert [r.model_dump() for r in result.unwrap()] == [r.model_dump() for r in exp.unwrap()]
        else:
            assert isinstance(result.failure(), type(exp.failure()))
            assert result.failure().algorithm_name == exp.failure().algorithm_name
            assert result.failure().benchmark_name == exp.failure().benchmark_name
