from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful

from luna_bench._internal.domain_models import AlgorithmResultDomain, FeatureResultDomain, MetricResultDomain
from luna_bench._internal.usecases.benchmark.benchmark_reset import BenchmarkResetUcImpl
from luna_bench.entities import AlgorithmEntity, BenchmarkEntity, FeatureEntity, MetricEntity
from luna_bench.entities.algorithm_result_entity import AlgorithmResultEntity
from luna_bench.entities.enums import JobStatus, ResetLevel
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.entities.metric_result_entity import MetricResultEntity
from tests.unit.fixtures.mock_components import MockAlgorithm, MockFeature, MockMetric


if TYPE_CHECKING:
    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from tests.unit.fixtures.mock_database import SetupBenchmark


def _algo(name: str, status: JobStatus) -> AlgorithmEntity:
    return AlgorithmEntity(
        name=name,
        status=JobStatus.CREATED,
        algorithm=MockAlgorithm(),
        results={
            "model1": AlgorithmResultEntity.model_construct(
                meta_data=None,
                status=status,
                error=None,
                solution=None,
                task_id=None,
                retrival_data=None,
                model_id=0,
            )
        },
    )


def _feature(name: str, status: JobStatus) -> FeatureEntity:
    return FeatureEntity(
        name=name,
        status=JobStatus.CREATED,
        feature=MockFeature(),
        results={
            "model1": FeatureResultEntity.model_construct(
                processing_time_ms=0,
                model_name="model1",
                status=status,
                error=None,
                result=None,
            )
        },
    )


def _metric(name: str, status: JobStatus) -> MetricEntity:
    return MetricEntity(
        name=name,
        status=JobStatus.CREATED,
        metric=MockMetric(),
        results={
            "model1": {
                "algo1": MetricResultEntity.model_construct(
                    processing_time_ms=0,
                    model_name="model1",
                    algorithm_name="algo1",
                    status=status,
                    error=None,
                    result=None,
                )
            }
        },
    )


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
        "benchmark_name",
        ["existing", "non-existing"],
    )
    def test_all_reset(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
        benchmark_name: str,
    ) -> None:
        if benchmark_name == "non-existing":
            result = usecase.benchmark_reset_uc()(_entity("non-existing"), mode=ResetLevel.ALL)
            assert is_successful(result)
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

        result = usecase.benchmark_reset_uc()(entity, mode=ResetLevel.ALL)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()(benchmark_name).unwrap()
        for a in reloaded.algorithms:
            assert len(a.results) == 0
        for f in reloaded.features:
            assert len(f.results) == 0
        for m in reloaded.metrics:
            assert len(m.results) == 0

    def test_unfinished_reset(
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

        result = usecase.benchmark_reset_uc()(entity, mode=ResetLevel.UNFINISHED)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(reloaded.algorithms[0].results) == 0
        assert len(reloaded.metrics[0].results) == 0

    def test_unfinished_reset_clears_failed_metric(
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

        result = usecase.benchmark_reset_uc()(entity, mode=ResetLevel.UNFINISHED)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(reloaded.algorithms[0].results) > 0
        assert len(reloaded.metrics[0].results) == 0

    def test_unfinished_reset_noop_when_all_done(
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

        result = usecase.benchmark_reset_uc()(entity, mode=ResetLevel.UNFINISHED)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(reloaded.algorithms[0].results) > 0

    def test_failed_reset(
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
        tx.feature.set_result(
            "existing",
            "existing",
            FeatureResultDomain.model_construct(
                processing_time_ms=100,
                model_name=setup_benchmark.model_name,
                result=None,
                status=JobStatus.DONE,
                error=None,
            ),
        )

        entity = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(entity.algorithms[0].results) > 0
        assert len(entity.features[0].results) > 0

        result = usecase.benchmark_reset_uc()(entity, mode=ResetLevel.FAILED)
        assert is_successful(result)

        reloaded = usecase.benchmark_load_uc()("existing").unwrap()
        assert len(reloaded.algorithms[0].results) == 0
        assert len(reloaded.features[0].results) > 0

    def test_failed_reset_noop_when_nothing_failed(
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

        result = usecase.benchmark_reset_uc()(entity, mode=ResetLevel.FAILED)
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

        bench.reset(mode="All")
        assert len(bench.algorithms[0].results) == 0

    def test_reset_non_existing_via_benchmark_class(
        self,
        usecase: UsecaseContainer,  # noqa: ARG002
        setup_benchmark: SetupBenchmark,  # noqa: ARG002
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
        # Components have no results — reset is a no-op, not an error
        bench.reset(mode="All")
        assert len(bench.algorithms[0].results) == 0

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


class TestGetResetComponentNames:
    """Unit tests for ``BenchmarkResetUcImpl._get_reset_component_names``."""

    @pytest.mark.parametrize(
        ("mode", "algorithms", "features", "metrics", "exp_algos", "exp_feats", "exp_metrics"),
        [
            pytest.param(
                ResetLevel.ALL,
                [_algo("a", JobStatus.DONE)],
                [_feature("f", JobStatus.DONE)],
                [_metric("m", JobStatus.DONE)],
                ["a"],
                ["f"],
                ["m"],
                id="all-returns-all",
            ),
            pytest.param(
                ResetLevel.ALL,
                [AlgorithmEntity(name="a", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={})],
                [FeatureEntity(name="f", status=JobStatus.CREATED, feature=MockFeature(), results={})],
                [MetricEntity(name="m", status=JobStatus.CREATED, metric=MockMetric(), results={})],
                [],
                [],
                [],
                id="all-empty-results-nothing",
            ),
            pytest.param(
                ResetLevel.UNFINISHED,
                [
                    _algo("done", JobStatus.DONE),
                    _algo("failed", JobStatus.FAILED),
                    _algo("created", JobStatus.CREATED),
                ],
                [_feature("f", JobStatus.DONE)],
                [_metric("m", JobStatus.DONE)],
                ["failed", "created"],
                [],
                ["m"],  # metric cascaded
                id="unfinished-returns-only-non-done",
            ),
            pytest.param(
                ResetLevel.UNFINISHED,
                [_algo("a", JobStatus.DONE)],
                [_feature("f", JobStatus.DONE)],
                [_metric("m", JobStatus.DONE)],
                [],
                [],
                [],
                id="unfinished-noop-when-all-done",
            ),
            pytest.param(
                ResetLevel.FAILED,
                [
                    _algo("done", JobStatus.DONE),
                    _algo("failed", JobStatus.FAILED),
                ],
                [_feature("failed_f", JobStatus.FAILED)],
                [_metric("m", JobStatus.FAILED)],
                ["failed"],
                ["failed_f"],
                ["m"],
                id="failed-returns-only-failed",
            ),
            pytest.param(
                ResetLevel.FAILED,
                [_algo("failed", JobStatus.FAILED)],
                [_feature("f", JobStatus.DONE)],
                [_metric("m", JobStatus.DONE)],
                ["failed"],
                [],
                ["m"],  # metric cascaded
                id="failed-metric-cascade",
            ),
            pytest.param(
                ResetLevel.FAILED,
                [_algo("a", JobStatus.DONE)],
                [_feature("f", JobStatus.DONE)],
                [_metric("m", JobStatus.DONE)],
                [],
                [],
                [],
                id="failed-noop-when-nothing-failed",
            ),
        ],
    )
    def test_get_reset_component_names(
        self,
        mode: ResetLevel,
        algorithms: list[AlgorithmEntity],
        features: list[FeatureEntity],
        metrics: list[MetricEntity],
        exp_algos: list[str],
        exp_feats: list[str],
        exp_metrics: list[str],
    ) -> None:
        entity = BenchmarkEntity(
            name="test",
            modelset=None,
            algorithms=algorithms,
            features=features,
            metrics=metrics,
            plots=[],
        )
        algos, feats, mets = BenchmarkResetUcImpl._get_reset_component_names(entity, mode)
        assert algos == exp_algos
        assert feats == exp_feats
        assert mets == exp_metrics
