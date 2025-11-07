from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces import IPlot
from luna_bench._internal.usecases.benchmark.enums import UseCaseErrorHandlingMode
from luna_bench._internal.user_models import BenchmarkUserModel, PlotUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.fixtures.mock_components import MockPlot, MockPlotWithValidationError, UnregisteredPlot

if TYPE_CHECKING:
    from pydantic import ValidationError

    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError


def _empty_plot(name: str, plot: IPlot[Any]) -> PlotUserModel:
    return PlotUserModel(
        name=name,
        status=JobStatus.CREATED,
        plot=plot,
    )


class TestPlot:
    @pytest.fixture()
    @staticmethod
    def default_usecase(usecase: UsecaseContainer) -> UsecaseContainer:
        create_default: Result[
            BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = usecase.benchmark_create_uc()(benchmark_name="existing")
        assert is_successful(create_default)
        create_default_plot = usecase.benchmark_add_plot_uc()(
            benchmark_name="existing", name="existing", plot=MockPlot()
        )
        assert is_successful(create_default_plot)

        return usecase

    @pytest.mark.parametrize(
        ("benchmark_name", "plot_name", "plot", "exp"),
        [
            ("non-existing", "existing", MockPlot(), Failure(DataNotExistError())),
            ("existing", "existing", MockPlot(), Failure(DataNotUniqueError())),
            ("existing", "non-existing", UnregisteredPlot(), Failure(UnknownComponentError("", IPlot))),
            ("existing", "non-existing", MockPlot(), Success(_empty_plot("non-existing", MockPlot()))),
        ],
    )
    def test_add(
        self,
        default_usecase: UsecaseContainer,
        benchmark_name: str,
        plot_name: str,
        plot: IPlot[Any],
        exp: Result[
            PlotUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[
            PlotUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = default_usecase.benchmark_add_plot_uc()(benchmark_name, plot_name, plot)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "plot_name", "exp"),
        [
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
            ("existing", "existing", Success(None)),
        ],
    )
    def test_remove(
        self,
        default_usecase: UsecaseContainer,
        benchmark_name: str,
        plot_name: str,
        exp: Result[
            PlotUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = default_usecase.benchmark_remove_plot_uc()(
            benchmark_name, plot_name
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("error_handling_mode", "plot", "exp"),
        [
            (UseCaseErrorHandlingMode.FAIL_ON_ERROR, MockPlot(), Failure(UnknownLunaBenchError(NotImplementedError()))),
            (UseCaseErrorHandlingMode.FAIL_ON_ERROR, MockPlotWithValidationError(), Failure(PlotRunError())),
            (UseCaseErrorHandlingMode.CONTINUE_ON_ERROR, MockPlotWithValidationError(), Success(None)),
        ],
    )
    def test_run_plots(
        self,
        default_usecase: UsecaseContainer,
        error_handling_mode: UseCaseErrorHandlingMode,
        plot: IPlot[Any],
        exp: Result[
            PlotUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        benchmark = BenchmarkUserModel(
            name="test",
            modelset=None,
            features=[],
            algorithms=[],
            metrics=[],
            plots=[_empty_plot("test", plot)],
        )

        result = default_usecase.benchmark_run_plots_uc()(benchmark, error_handling_mode)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))
