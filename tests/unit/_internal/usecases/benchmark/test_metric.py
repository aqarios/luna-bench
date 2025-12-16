from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.user_models import FeatureUserModel, MetricUserModel
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench.base_components import BaseMetric
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from tests.unit.fixtures.mock_components import MockMetric, MockMetricError, UnregisteredMetric

if TYPE_CHECKING:
    from luna_quantum import Solution
    from pydantic import ValidationError

    from luna_bench._internal.mappers.container import MapperContainer
    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError
    from tests.unit.fixtures.mock_database import SetupBenchmark


def _empty_metric(name: str, metric: BaseMetric) -> MetricUserModel:
    return MetricUserModel(
        name=name,
        status=JobStatus.CREATED,
        metric=metric,
        results={},
    )


class TestMetric:
    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "metric", "exp"),
        [
            ("non-existing", "existing", MockMetric(), Failure(DataNotExistError())),
            ("existing", "existing", MockMetric(), Failure(DataNotUniqueError())),
            ("existing", "non-existing", UnregisteredMetric(), Failure(UnknownComponentError("", BaseMetric))),
            ("existing", "non-existing", MockMetric(), Success(_empty_metric("non-existing", MockMetric()))),
        ],
    )
    def test_add(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        metric_name: str,
        metric: BaseMetric,
        exp: Result[
            MetricUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[
            MetricUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = usecase.benchmark_add_metric_uc()(benchmark_name, metric_name, metric)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
            ("existing", "existing", Success(None)),
        ],
    )
    def test_remove(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        metric_name: str,
        exp: Result[
            FeatureUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = usecase.benchmark_remove_metric_uc()(
            benchmark_name, metric_name
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("metric", "exp"),
        [
            (_empty_metric("bla", MockMetric()), Failure(RunMetricMissingError("existing", "bla"))),
            (None, Success(None)),
            ("existing", Success(None)),
        ],
    )
    def test_run(
        self,
        setup_benchmark: SetupBenchmark,
        usecase: UsecaseContainer,
        metric: MetricUserModel | str | None,
        mapper: MapperContainer,
        solution: Solution,
        exp: Result[None, RunMetricMissingError | RunModelsetMissingError],
    ) -> None:
        benchmark = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark).unwrap()

        ## Prepare fake results for all algorithms
        num_metrics_to_calculate = 0
        for a in benchmark.algorithms:
            assert benchmark.modelset is not None
            for model in benchmark.modelset.models:
                num_metrics_to_calculate += 1
                a.results[model.name] = AlgorithmResultUserModel(
                    meta_data=None,
                    status=JobStatus.DONE,
                    error=None,
                    solution=solution,
                    task_id=None,
                    retrival_data=None,
                    model_id=model.id,
                )

        if isinstance(metric, str):
            metric = next((f for f in benchmark.metrics if f.name == metric), None)

        result = usecase.benchmark_run_metric_uc()(benchmark=benchmark, metric=metric)

        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()

            for m in benchmark.metrics:
                if metric is None or metric.name == m.name:
                    assert len(m.results) == num_metrics_to_calculate
                    for r in m.results.values():
                        assert r.status == JobStatus.DONE
                else:
                    assert len(m.results) == 0

        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_run_rerun(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
        solution: Solution,
    ) -> None:
        benchmark = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark).unwrap()
        for a in benchmark.algorithms:
            assert benchmark.modelset is not None
            for model in benchmark.modelset.models:
                a.results[model.name] = AlgorithmResultUserModel(
                    meta_data=None,
                    status=JobStatus.DONE,
                    error=None,
                    solution=solution,
                    task_id=None,
                    retrival_data=None,
                    model_id=model.id,
                )
        result = usecase.benchmark_run_metric_uc()(benchmark=benchmark, metric=benchmark.metrics[0])

        assert is_successful(result)
        for m in benchmark.metrics:
            for r in m.results.values():
                assert r.status is JobStatus.DONE

        result_2 = usecase.benchmark_run_metric_uc()(benchmark=benchmark, metric=benchmark.metrics[0])

        assert is_successful(result_2)

        benchmark2 = usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()

        assert benchmark.metrics == benchmark2.metrics

    def test_run_algorithm_not_done(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
        solution: Solution,
    ) -> None:
        benchmark = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark).unwrap()
        for a in benchmark.algorithms:
            assert benchmark.modelset is not None
            for model in benchmark.modelset.models:
                a.results[model.name] = AlgorithmResultUserModel(
                    meta_data=None,
                    status=JobStatus.RUNNING,
                    error=None,
                    solution=solution,
                    task_id=None,
                    retrival_data=None,
                    model_id=model.id,
                )
        result = usecase.benchmark_run_metric_uc()(benchmark=benchmark, metric=benchmark.metrics[0])

        assert is_successful(result)
        for m in benchmark.metrics:
            assert len(m.results) == 0

    def test_run_no_solution_present(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> None:
        benchmark = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark).unwrap()
        for a in benchmark.algorithms:
            assert benchmark.modelset is not None
            for model in benchmark.modelset.models:
                a.results[model.name] = AlgorithmResultUserModel(
                    meta_data=None,
                    status=JobStatus.DONE,
                    error=None,
                    solution=None,
                    task_id=None,
                    retrival_data=None,
                    model_id=model.id,
                )
        result = usecase.benchmark_run_metric_uc()(benchmark=benchmark, metric=benchmark.metrics[0])

        assert is_successful(result)
        for m in benchmark.metrics:
            assert len(m.results) == 0

    def test_run_failing_metric(
        self,
        usecase: UsecaseContainer,
        setup_benchmark: SetupBenchmark,
        mapper: MapperContainer,
    ) -> None:
        benchmark = mapper.benchmark_mapper().to_user_model(setup_benchmark.benchmark).unwrap()
        for a in benchmark.algorithms:
            assert benchmark.modelset is not None
            for model in benchmark.modelset.models:
                a.results[model.name] = AlgorithmResultUserModel(
                    meta_data=None,
                    status=JobStatus.DONE,
                    error=None,
                    solution=None,
                    task_id=None,
                    retrival_data=None,
                    model_id=model.id,
                )
        metric_result = usecase.benchmark_add_metric_uc()(
            benchmark_name=benchmark.name, name="error metric", metric=MockMetricError()
        )
        assert is_successful(metric_result)
        metric = metric_result.unwrap()
        benchmark.metrics.append(metric)
        result = usecase.benchmark_run_metric_uc()(benchmark=benchmark, metric=metric)

        assert is_successful(result)
        for m in benchmark.metrics:
            assert len(m.results) == 0
