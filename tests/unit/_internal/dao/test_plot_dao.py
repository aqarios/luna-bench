from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import JobStatus, PlotConfigDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError

if TYPE_CHECKING:
    from luna_bench._internal.dao import StorageTransaction
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


class TestPlotDAO:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: StorageTransaction) -> StorageTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        empty_transaction.modelset.create(modelset_name="existing")
        return empty_transaction

    @pytest.mark.parametrize(
        ("name", "exp"),
        [
            (
                "existing",
                Success(
                    PlotConfigDomain(
                        id=1,
                        name="existing",
                        status=JobStatus.CREATED,
                        config_data=PlotConfigDomain.PlotConfig(tester="tester"),
                    )
                ),
            ),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_plot(setup_transaction: StorageTransaction, name: str, exp: Result) -> None:
        result = setup_transaction.plot.add_plot(name, "existing", PlotConfigDomain.PlotConfig(tester="tester"))
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(name).unwrap().plots) == 1
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("name", "exp"),
        [
            (
                "existing",
                Success(
                    PlotConfigDomain(
                        id=1,
                        config_data=PlotConfigDomain.PlotConfig(tester="tester"),
                        name="existing",
                        status=JobStatus.CREATED,
                    )
                ),
            ),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_load_plot(setup_transaction: StorageTransaction, name: str, exp: Result) -> None:
        result_add = setup_transaction.plot.add_plot(
            "existing", "existing", PlotConfigDomain.PlotConfig(tester="tester")
        )
        assert type(result_add) is type(Success(None))

        result: Result[PlotConfigDomain, DataNotExistError | UnknownLunaBenchError] = setup_transaction.plot.load(
            "existing", name
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
    def test_remove_plot(
        setup_transaction: StorageTransaction, benchmark_name: str, plot_name: str, exp: Result
    ) -> None:
        result_add = setup_transaction.plot.add_plot(
            "existing", "existing", PlotConfigDomain.PlotConfig(tester="tester")
        )
        assert type(result_add) is type(Success(None))
        assert len(setup_transaction.benchmark.load("existing").unwrap().plots) == 1

        result = setup_transaction.plot.remove_plot(benchmark_name, plot_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load("existing").unwrap().plots) == 0
        else:
            assert isinstance(result.failure(), type(exp.failure()))
