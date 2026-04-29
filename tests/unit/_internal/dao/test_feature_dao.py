from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import (
    BenchmarkStatus,
    FeatureDomain,
    FeatureResultDomain,
)
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.types import FeatureResult
from tests.unit.fixtures.mock_config import MockConfig

if TYPE_CHECKING:
    from luna_bench._internal.dao import DaoTransaction


class TestFeatureDAO:
    _saved_feature_domain: FeatureDomain

    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.modelset.create(modelset_name="existing")
        empty_transaction.model.get_or_create(model_name="existing", model_hash=1, binary=b"")
        empty_transaction.benchmark.create(benchmark_name="existing")
        TestFeatureDAO._saved_feature_domain = empty_transaction.feature.add(
            benchmark_name="existing",
            feature_name="existing",
            registered_id="existing",
            feature_config=ArbitraryDataDomain.model_validate(
                MockConfig(something="xD").model_dump(), from_attributes=True
            ),
        ).unwrap()

        return empty_transaction

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "non-existing",
                Success(
                    FeatureDomain(
                        name="non-existing",
                        status=JobStatus.CREATED,
                        results={},
                        config_data=RegisteredDataDomain(
                            registered_id="existing",
                            data=ArbitraryDataDomain.model_validate(
                                MockConfig(something="xD").model_dump(), from_attributes=True
                            ),
                        ),
                    )
                ),
            ),
            ("existing", "existing", Failure(DataNotUniqueError())),
            ("non-existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_feature(
        setup_transaction: DaoTransaction,
        benchmark_name: str,
        metric_name: str,
        exp: Result[None, DataNotUniqueError | DataNotExistError],
    ) -> None:
        result = setup_transaction.feature.add(
            benchmark_name,
            metric_name,
            "existing",
            ArbitraryDataDomain.model_validate(MockConfig(something="xD").model_dump(), from_attributes=True),
        )
        assert is_successful(result) == is_successful(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().features) == 2
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("existing", "non-existing", Failure(DataNotExistError())),
            ("non-existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_load_feature(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotUniqueError]
    ) -> None:
        result = setup_transaction.feature.load(benchmark_name, metric_name)
        assert is_successful(result) == is_successful(exp)

        if is_successful(exp):
            assert result.unwrap() == TestFeatureDAO._saved_feature_domain
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
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
    def test_remove_feature(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotUniqueError]
    ) -> None:
        result = setup_transaction.feature.remove(benchmark_name, metric_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().features) == 0
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
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
    def test_update_feature(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotUniqueError]
    ) -> None:
        result = setup_transaction.feature.update(
            benchmark_name,
            metric_name,
            "existing2",
            ArbitraryDataDomain.model_validate(MockConfig(something="xD2").model_dump(), from_attributes=True),
        )
        assert is_successful(result) == is_successful(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            r = setup_transaction.benchmark.load(benchmark_name).unwrap().features[0]

            assert r.status == JobStatus.CREATED
            assert getattr(r.config_data.data, "something", "nope") == "xD2"
            assert r.config_data.registered_id == "existing2"
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
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
    def test_update_feature_status(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotUniqueError]
    ) -> None:
        result = setup_transaction.feature.update_status(benchmark_name, metric_name, BenchmarkStatus.DONE)
        assert is_successful(result) == is_successful(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()

            assert setup_transaction.benchmark.load(benchmark_name).unwrap().features[0].status == JobStatus.DONE
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "feature_name", "result", "exp"),
        [
            (
                "existing",
                "existing",
                FeatureResultDomain.model_construct(
                    processing_time_ms=0,
                    model_name="existing",
                    status=JobStatus.CREATED,
                    error=None,
                    result=ArbitraryDataDomain(),
                ),
                Success(None),
            ),
            (
                "non-existing",
                "existing",
                FeatureResultDomain.model_construct(
                    processing_time_ms=0,
                    model_name="existing",
                    status=JobStatus.CREATED,
                    error=None,
                    result=FeatureResult.model_construct(something="xD"),  # type: ignore[call-arg]
                ),
                Failure(DataNotExistError()),
            ),
            (
                "existing",
                "non-existing",
                FeatureResultDomain.model_construct(
                    processing_time_ms=0,
                    model_name="existing",
                    status=JobStatus.CREATED,
                    error=None,
                    result=FeatureResult.model_construct(something="xD"),  # type: ignore[call-arg]
                ),
                Failure(DataNotExistError()),
            ),
        ],
    )
    def test_result_storage(
        self,
        setup_transaction: DaoTransaction,
        benchmark_name: str,
        feature_name: str,
        result: FeatureResultDomain,
        exp: Result[FeatureResultDomain, DataNotExistError | DataNotUniqueError],
    ) -> None:
        set_result = setup_transaction.feature.set_result(benchmark_name, feature_name, result)
        assert is_successful(set_result) == is_successful(exp)

        if is_successful(exp):
            assert {result.model_name: result} == setup_transaction.feature.load(
                benchmark_name, feature_name
            ).unwrap().results
        else:
            assert isinstance(set_result.failure(), type(exp.failure()))

        remove = setup_transaction.feature.remove_result(benchmark_name, feature_name)

        assert is_successful(remove) is is_successful(exp)

        if is_successful(exp):
            assert setup_transaction.feature.load(benchmark_name, feature_name).unwrap().results == {}
        else:
            assert isinstance(remove.failure(), type(exp.failure()))
