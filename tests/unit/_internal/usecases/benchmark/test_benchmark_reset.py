from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import AlgorithmResultDomain, FeatureResultDomain, MetricResultDomain
from luna_bench.entities import AlgorithmEntity, BenchmarkEntity, FeatureEntity, MetricEntity
from luna_bench.entities.enums import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from tests.unit.fixtures.mock_components import MockAlgorithm, MockFeature, MockMetric

if TYPE_CHECKING:
    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.unknown_error import UnknownLunaBenchError
    from tests.unit.fixtures.mock_database import SetupBenchmark


def _entity(name: str) -> BenchmarkEntity:
    return BenchmarkEntity(
        name=name,
        modelset=None,
        features=[FeatureEntity(name="f", status=JobStatus.CREATED, feature=MockFeature(), results={})],
        algorithms=[AlgorithmEntity(name="a", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={})],
        metrics=[MetricEntity(name="m", status=JobStatus.CREATED, metric=MockMetric(), results={})],
        plots=[],
    )


class TestBenchmarkReset:
    @pytest.mark.parametrize(
        ("benchmark_name", "exp"),
        [
            ("existing", Success(None)),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    def test_hard_reset(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
        benchmark_name: str,
        exp: Result[None, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        if benchmark_name == "non-existing":
            result = usecase.benchmark_reset_uc()(_entity("non-existing"), soft=False)
            assert type(result) is type(exp)
            if not is_successful(exp):
                assert isinstance(result.failure(), type(exp.failure()))
            return

        tx = setup_benchmark.transaction
        tx.algorithm.set_result(
            benchmark_name,
            "existing",
            AlgorithmResultDomain.model_construct(
                meta_data=None,
                model_id=setup_benchmark.model_metadata.id,
                status=JobStatus.DONE,
                error=None,
                task_id=None,
                retrival_data=None,
            ),
        )
        tx.feature.set_result(
            benchmark_name,
            "existing",
            FeatureResultDomain.model_construct(
                processing_time_ms=100,
                model_name=setup_benchmark.model_name,
                result=None,
                status=JobStatus.DONE,
                error=None,
            ),
        )
        tx.metric.set_result(
            benchmark_name,
            "existing",
            MetricResultDomain.model_construct(
                processing_time_ms=100,
                model_name=setup_benchmark.model_name,
                algorithm_name="existing",
                result=None,
                status=JobStatus.DONE,
                error=None,
            ),
        )

        entity = usecase.benchmark_load_uc()(benchmark_name).unwrap()
        assert len(entity.algorithms[0].results) > 0

        result = usecase.benchmark_reset_uc()(entity, soft=False)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()(benchmark_name).unwrap()
        for a in reloaded.algorithms:
            assert len(a.results) == 0
        for f in reloaded.features:
            assert len(f.results) == 0
        for m in reloaded.metrics:
            assert len(m.results) == 0

    def test_soft_reset(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
    ) -> None:
        tx = setup_benchmark.transaction
        tx.algorithm.set_result(
            "existing",
            "existing",
            AlgorithmResultDomain.model_construct(
                meta_data=None,
                model_id=setup_benchmark.model_metadata.id,
                status=JobStatus.FAILED,
                error=None,
                task_id=None,
                retrival_data=None,
            ),
        )
        tx.metric.set_result(
            "existing",
            "existing",
            MetricResultDomain.model_construct(
                processing_time_ms=100,
                model_name=setup_benchmark.model_name,
                algorithm_name="existing",
                result=None,
                status=JobStatus.DONE,
                error=None,
            ),
        )

        entity = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(entity.algorithms[0].results) > 0

        result = usecase.benchmark_reset_uc()(entity, soft=True)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(reloaded.algorithms[0].results) == 0
        assert len(reloaded.metrics[0].results) == 0

    def test_soft_reset_clears_failed_metric(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
    ) -> None:
        tx = setup_benchmark.transaction
        tx.algorithm.set_result(
            "existing",
            "existing",
            AlgorithmResultDomain.model_construct(
                meta_data=None,
                model_id=setup_benchmark.model_metadata.id,
                status=JobStatus.DONE,
                error=None,
                task_id=None,
                retrival_data=None,
            ),
        )
        tx.metric.set_result(
            "existing",
            "existing",
            MetricResultDomain.model_construct(
                processing_time_ms=100,
                model_name=setup_benchmark.model_name,
                algorithm_name="existing",
                result=None,
                status=JobStatus.FAILED,
                error=None,
            ),
        )

        entity = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(entity.algorithms[0].results) > 0
        assert len(entity.metrics[0].results) > 0

        result = usecase.benchmark_reset_uc()(entity, soft=True)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(reloaded.algorithms[0].results) > 0
        assert len(reloaded.metrics[0].results) == 0

    def test_soft_reset_noop_when_all_done(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
    ) -> None:
        tx = setup_benchmark.transaction
        tx.algorithm.set_result(
            "existing",
            "existing",
            AlgorithmResultDomain.model_construct(
                meta_data=None,
                model_id=setup_benchmark.model_metadata.id,
                status=JobStatus.DONE,
                error=None,
                task_id=None,
                retrival_data=None,
            ),
        )

        entity = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(entity.algorithms[0].results) > 0

        result = usecase.benchmark_reset_uc()(entity, soft=True)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(reloaded.algorithms[0].results) > 0

    def test_reset_via_benchmark_class(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
    ) -> None:
        from luna_bench import Benchmark

        tx = setup_benchmark.transaction
        tx.algorithm.set_result(
            "existing",
            "existing",
            AlgorithmResultDomain.model_construct(
                meta_data=None,
                model_id=setup_benchmark.model_metadata.id,
                status=JobStatus.DONE,
                error=None,
                task_id=None,
                retrival_data=None,
            ),
        )

        entity = usecase.benchmark_load_uc()("existing").unwrap()
        bench = Benchmark.model_validate(entity, from_attributes=True)
        assert len(bench.algorithms[0].results) > 0

        bench.reset()
        assert len(bench.algorithms[0].results) == 0

    def test_reset_non_existing_via_benchmark_class(
        self,
        usecase: UsecaseContainer,  # noqa: ARG002
    ) -> None:
        from luna_bench import Benchmark

        entity = BenchmarkEntity(
            name="existing",
            modelset=None,
            algorithms=[
                AlgorithmEntity(
                    name="no_such_algo",
                    status=JobStatus.CREATED,
                    algorithm=MockAlgorithm(),
                    results={},
                )
            ],
            features=[
                FeatureEntity(
                    name="no_such_feature",
                    status=JobStatus.CREATED,
                    feature=MockFeature(),
                    results={},
                )
            ],
            metrics=[
                MetricEntity(
                    name="no_such_metric",
                    status=JobStatus.CREATED,
                    metric=MockMetric(),
                    results={},
                )
            ],
            plots=[],
        )
        bench = Benchmark.model_validate(entity, from_attributes=True)
        with pytest.raises(DataNotExistError):
            bench.reset()

    def test_retry_uncompleted_via_benchmark_class(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
    ) -> None:
        from luna_bench import Benchmark

        tx = setup_benchmark.transaction
        tx.algorithm.set_result(
            "existing",
            "existing",
            AlgorithmResultDomain.model_construct(
                meta_data=None,
                model_id=setup_benchmark.model_metadata.id,
                status=JobStatus.FAILED,
                error=None,
                task_id=None,
                retrival_data=None,
            ),
        )

        entity = usecase.benchmark_load_uc()("existing").unwrap()
        bench = Benchmark.model_validate(entity, from_attributes=True)
        assert len(bench.algorithms[0].results) > 0

        bench.run(retry_uncompleted=True)
