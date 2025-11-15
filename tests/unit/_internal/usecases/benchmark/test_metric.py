from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.user_models import FeatureUserModel, MetricUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from tests.unit.fixtures.mock_components import MockMetric, UnregisteredMetric

if TYPE_CHECKING:
    from pydantic import ValidationError

    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


def _empty_metric(name: str, metric: IMetric) -> MetricUserModel:
    return MetricUserModel(
        name=name,
        status=JobStatus.CREATED,
        metric=metric,
    )


class TestMetric:
    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "metric", "exp"),
        [
            ("non-existing", "existing", MockMetric(), Failure(DataNotExistError())),
            ("existing", "existing", MockMetric(), Failure(DataNotUniqueError())),
            ("existing", "non-existing", UnregisteredMetric(), Failure(UnknownComponentError("", IMetric))),
            ("existing", "non-existing", MockMetric(), Success(_empty_metric("non-existing", MockMetric()))),
        ],
    )
    def test_add(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        metric_name: str,
        metric: IMetric,
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
