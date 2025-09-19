from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import JobStatus, PlotDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.benchmark_status_enum import BenchmarkStatus
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from tests.unit.fixtures.mock_config import MockConfig

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
            registered_id="existing",
            plot_config=MockConfig(something="xD"),
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
                    PlotDomain(
                        name="non-existing",
                        status=JobStatus.CREATED,
                        config_data=RegisteredDataDomain(
                            registered_id="existing",
                            data=MockConfig(something="xD"),
                        ),
                    )
                ),
            ),
            ("non-existing", "existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_plot(
        setup_transaction: DaoTransaction,
        benchmark_name: str,
        plot_name: str,
        exp: Result[PlotDomain, DataNotExistError],
    ) -> None:
        result = setup_transaction.plot.add(benchmark_name, plot_name, "existing", MockConfig(something="xD"))
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
                    PlotDomain(
                        config_data=RegisteredDataDomain(
                            registered_id="existing",
                            data=ArbitraryDataDomain.model_validate(
                                MockConfig(something="xD").model_dump(), from_attributes=True
                            ),
                        ),
                        name="existing",
                        status=JobStatus.CREATED,
                    )
                ),
            ),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_load_plot(setup_transaction: DaoTransaction, plot_name: str, exp: Result[None, DataNotExistError]) -> None:
        result: Result[PlotDomain, DataNotExistError | UnknownLunaBenchError] = setup_transaction.plot.load(
            "existing", plot_name
        )
        assert is_successful(result) == is_successful(exp)
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
        setup_transaction: DaoTransaction, benchmark_name: str, plot_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
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
    def test_update_plot(
        setup_transaction: DaoTransaction, benchmark_name: str, plot_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
        result = setup_transaction.plot.update(benchmark_name, plot_name, "existing2", MockConfig(something="xD2"))
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            plot = setup_transaction.benchmark.load(benchmark_name).unwrap().plots[0]
            assert plot.status == JobStatus.CREATED
            assert getattr(plot.config_data.data, "something", "nope") == "xD2"
            assert plot.config_data.registered_id == "existing2"
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
        setup_transaction: DaoTransaction, benchmark_name: str, plot_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
        result = setup_transaction.plot.update_status(benchmark_name, plot_name, BenchmarkStatus.DONE)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert setup_transaction.plot.load(benchmark_name, plot_name).unwrap().status == JobStatus.DONE
        else:
            assert isinstance(result.failure(), type(exp.failure()))
