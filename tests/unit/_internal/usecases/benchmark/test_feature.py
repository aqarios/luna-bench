from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.user_models import BenchmarkUserModel, FeatureUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from tests.unit.fixtures.mock_components import MockFeature, MockFeatureFailing, UnregisteredFeature

if TYPE_CHECKING:
    from luna_quantum import Model
    from pydantic import ValidationError

    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


def _empty_feature(name: str, feature: IFeature) -> FeatureUserModel:
    return FeatureUserModel(
        name=name,
        status=JobStatus.CREATED,
        feature=feature,
        results={},
    )


class TestFeature:
    @pytest.fixture()
    @staticmethod
    def default_usecase(usecase: UsecaseContainer) -> UsecaseContainer:
        create_default: Result[
            BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = usecase.benchmark_create_uc()(benchmark_name="existing")
        assert is_successful(create_default)
        create_default_feature = usecase.benchmark_add_feature_uc()(
            benchmark_name="existing", name="existing", feature=MockFeature()
        )
        assert is_successful(create_default_feature)

        create_default_feature2 = usecase.benchmark_add_feature_uc()(
            benchmark_name="existing", name="existing2", feature=MockFeature()
        )
        assert is_successful(create_default_feature2)

        create_default_modelset = usecase.modelset_create_uc()("existing")

        assert is_successful(create_default_modelset)

        return usecase

    @pytest.mark.parametrize(
        ("benchmark_name", "feature_name", "feature", "exp"),
        [
            ("non-existing", "existing", MockFeature(), Failure(DataNotExistError())),
            ("existing", "existing", MockFeature(), Failure(DataNotUniqueError())),
            ("existing", "non-existing", UnregisteredFeature(), Failure(UnknownComponentError("", IFeature))),
            ("existing", "non-existing", MockFeature(), Success(_empty_feature("non-existing", MockFeature()))),
        ],
    )
    def test_add(
        self,
        default_usecase: UsecaseContainer,
        benchmark_name: str,
        feature_name: str,
        feature: IFeature,
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
        result: Result[
            FeatureUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = default_usecase.benchmark_add_feature_uc()(benchmark_name, feature_name, feature)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "feature_name", "exp"),
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
        feature_name: str,
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
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = default_usecase.benchmark_remove_feature_uc()(
            benchmark_name, feature_name
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("feature", "modelset", "num_models", "exp"),
        [
            (_empty_feature("bla", MockFeature()), None, 1, Failure(RunFeatureMissingError("existing", "bla"))),
            (None, None, 1, Failure(RunModelsetMissingError("existing"))),
            (None, "existing", 1, Success(None)),
            ("existing", "existing", 1, Success(None)),
        ],
    )
    def test_run(
        self,
        default_usecase: UsecaseContainer,
        model: Model,
        modelset: str | None,
        feature: FeatureUserModel | str | None,
        num_models: int,
        exp: Result[None, RunFeatureMissingError | RunModelsetMissingError],
    ) -> None:
        if modelset:
            assert is_successful(
                default_usecase.benchmark_set_modelset_uc()(benchmark_name="existing", modelset_name=modelset)
            )
            for i in range(num_models):
                model.name = f"model_{i}"
                assert is_successful(default_usecase.model_add_uc()("existing", model))

        benchmark = default_usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()

        if isinstance(feature, str):
            feature = next((f for f in benchmark.features if f.name == feature), None)

        result = default_usecase.benchmark_run_feature_uc()(benchmark=benchmark, feature=feature)

        assert type(result) is type(exp)

        benchmark = default_usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()
        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()

            for f in benchmark.features:
                if feature is None or feature.name == f.name:
                    assert len(f.results) == num_models
                else:
                    assert len(f.results) == 0

        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_run_rerun(
        self,
        default_usecase: UsecaseContainer,
        model: Model,
    ) -> None:
        # check if rerun changes the results

        assert is_successful(default_usecase.model_add_uc()("existing", model))

        assert is_successful(
            default_usecase.benchmark_set_modelset_uc()(benchmark_name="existing", modelset_name="existing")
        )

        benchmark: BenchmarkUserModel = default_usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()

        assert benchmark.modelset is not None
        assert len(benchmark.modelset.models) > 0

        default_usecase.benchmark_run_feature_uc()(benchmark=benchmark, feature=None)

        for f in benchmark.features:
            for result in f.results.values():
                assert result.status is JobStatus.DONE

        default_usecase.benchmark_run_feature_uc()(benchmark=benchmark, feature=None)

        benchmark2 = default_usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()

        assert benchmark.features == benchmark2.features

    def test_run_failing_feature(
        self,
        default_usecase: UsecaseContainer,
        model: Model,
    ) -> None:
        assert is_successful(default_usecase.model_add_uc()("existing", model))

        assert is_successful(
            default_usecase.benchmark_set_modelset_uc()(benchmark_name="existing", modelset_name="existing")
        )
        default_usecase.benchmark_add_feature_uc()(
            benchmark_name="existing", name="failure", feature=MockFeatureFailing()
        ).unwrap()
        benchmark: BenchmarkUserModel = default_usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()

        feature = next((f for f in benchmark.features if f.name == "failure"), None)
        default_usecase.benchmark_run_feature_uc()(benchmark=benchmark, feature=feature)

        f = next((f for f in benchmark.features if f.name == "failure"), None)
        assert f is not None
        assert f.results["default_model"].status is JobStatus.FAILED
        assert f.results["default_model"].error == "Model failed."
