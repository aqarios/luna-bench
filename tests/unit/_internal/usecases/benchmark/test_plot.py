from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench.custom import BasePlot
from luna_bench.entities import BenchmarkEntity, PlotEntity
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from tests.unit.fixtures.mock_components import MockPlot, MockPlotWithError, UnregisteredPlot

if TYPE_CHECKING:
    from pydantic import ValidationError

    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError
    from tests.unit.fixtures.mock_database import SetupBenchmark


def _empty_plot(name: str, plot: BasePlot) -> PlotEntity:
    return PlotEntity(
        name=name,
        plot=plot,
    )


class TestPlot:
    @pytest.mark.parametrize(
        ("benchmark_name", "plot_name", "plot", "exp"),
        [
            ("non-existing", "existing", MockPlot(), Failure(DataNotExistError())),
            ("existing", "existing", MockPlot(), Failure(DataNotUniqueError())),
            ("existing", "non-existing", UnregisteredPlot(), Failure(UnknownComponentError("", BasePlot))),
            ("existing", "non-existing", MockPlot(), Success(_empty_plot("non-existing", MockPlot()))),
        ],
    )
    def test_add(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        plot_name: str,
        plot: BasePlot,
        exp: Result[
            PlotEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[
            PlotEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = usecase.benchmark_add_plot_uc()(benchmark_name, plot_name, plot)

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
        usecase: UsecaseContainer,
        benchmark_name: str,
        plot_name: str,
        exp: Result[
            PlotEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = usecase.benchmark_remove_plot_uc()(
            benchmark_name, plot_name
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("plot", "exp"),
        [
            (MockPlot(), Success(None)),
            (MockPlotWithError(), Success(None)),
        ],
    )
    def test_run_plots(
        self,
        setup_benchmark: SetupBenchmark,
        usecase: UsecaseContainer,
        plot: BasePlot,
        exp: Result[
            PlotEntity,
            DataNotUniqueError | DataNotExistError | UnknownLunaBenchError | UnknownComponentError | ValidationError,
        ],
    ) -> None:

        cast("Any", setup_benchmark.benchmark).plots = [_empty_plot("test", plot)]

        result = usecase.benchmark_run_plots_uc()(cast("BenchmarkEntity", setup_benchmark.benchmark))

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_run_plot_without_modelset(
        self,
        usecase: UsecaseContainer,
    ) -> None:
        benchmark = BenchmarkEntity(
            name="test_no_modelset",
            modelset=None,
            features=[],
            metrics=[],
            algorithms=[],
            plots=[_empty_plot("test", MockPlot())],
        )
        result = usecase.benchmark_run_plots_uc()(benchmark=benchmark)
        assert is_successful(result)
