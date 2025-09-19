from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import JobStatus, PlotConfigDomain
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.dao import DaoTransaction
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


class TestPlotDAO:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")

        empty_transaction.benchmark.create(benchmark_name="existing")
        empty_transaction.plot.add(
            benchmark_name="existing",
            plot_name="existing",
            plot_config=PlotConfigDomain.PlotConfig(something="xD"),
        ).unwrap()

        return empty_transaction

    @pytest.mark.parametrize(
        ("benchmark_name", "plot_name", "exp"),
        [
            (
                "existing",
                "existing",
                Failure(DataNotUniqueError()),
            ),
            (
                "existing",
                "non-existing",
                Success(
                    PlotConfigDomain(
                        id=2,
                        name="non-existing",
                        status=JobStatus.CREATED,
                        config_data=PlotConfigDomain.PlotConfig(tester="tester"),
                    )
                ),
            ),
            ("non-existing", "existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_plot(setup_transaction: DaoTransaction, benchmark_name: str, plot_name: str, exp: Result) -> None:
        result = setup_transaction.plot.add(benchmark_name, plot_name, PlotConfigDomain.PlotConfig(tester="tester"))
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().plots) == 2
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("plot_name", "exp"),
        [
            (
                "existing",
                Success(
                    PlotConfigDomain(
                        id=1,
                        config_data=PlotConfigDomain.PlotConfig(something="xD"),
                        name="existing",
                        status=JobStatus.CREATED,
                    )
                ),
            ),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_load_plot(setup_transaction: DaoTransaction, plot_name: str, exp: Result) -> None:
        result: Result[PlotConfigDomain, DataNotExistError | UnknownLunaBenchError] = setup_transaction.plot.load(
            "existing", plot_name
        )
        assert type(result) is type(exp)
        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "plot_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_remove_plot(setup_transaction: DaoTransaction, benchmark_name: str, plot_name: str, exp: Result) -> None:
        result = setup_transaction.plot.remove(benchmark_name, plot_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load("existing").unwrap().plots) == 0
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "plot_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_update_plot(setup_transaction: DaoTransaction, benchmark_name: str, plot_name: str, exp: Result) -> None:
        result = setup_transaction.plot.update(benchmark_name, plot_name, PlotConfigDomain.PlotConfig(something="xD2"))
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert setup_transaction.benchmark.load(benchmark_name).unwrap().plots[0].status == JobStatus.CREATED
            assert setup_transaction.benchmark.load(benchmark_name).unwrap().plots[0].config_data.something == "xD2"
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "plot_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_update_plot_status(
        setup_transaction: DaoTransaction, benchmark_name: str, plot_name: str, exp: Result
    ) -> None:
        result = setup_transaction.plot.update_status(benchmark_name, plot_name, JobStatus.DONE)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert setup_transaction.plot.load(benchmark_name, plot_name).unwrap().status == JobStatus.DONE
        else:
            assert isinstance(result.failure(), type(exp.failure()))
