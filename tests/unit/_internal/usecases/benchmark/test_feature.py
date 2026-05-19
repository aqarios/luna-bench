from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench.custom import BaseFeature
from luna_bench.entities import BenchmarkEntity, FeatureEntity, JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from tests.unit.fixtures.mock_components import MockFeature, MockFeatureFailing, UnregisteredFeature

if TYPE_CHECKING:
    from luna_model import Model
    from pydantic import ValidationError

    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


def _empty_feature(name: str, feature: BaseFeature) -> FeatureEntity:
    return FeatureEntity(
        name=name,
        status=JobStatus.CREATED,
        feature=feature,
        results={},
    )


class TestFeature:
    @pytest.mark.parametrize(
        ("benchmark_name", "feature_name", "feature", "exp"),
        [
            ("non-existing", "existing", MockFeature(), Failure(DataNotExistError())),
            ("existing", "existing", MockFeature(), Failure(DataNotUniqueError())),
            ("existing", "non-existing", UnregisteredFeature(), Failure(UnknownComponentError("", BaseFeature))),
            ("existing", "non-existing", MockFeature(), Success(_empty_feature("non-existing", MockFeature()))),
        ],
    )
    def test_add(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        feature_name: str,
        feature: BaseFeature,
        exp: Result[
            FeatureEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[
            FeatureEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = usecase.benchmark_add_feature_uc()(benchmark_name, feature_name, feature)

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
        usecase: UsecaseContainer,
        benchmark_name: str,
        feature_name: str,
        exp: Result[
            FeatureEntity,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = usecase.benchmark_remove_feature_uc()(
            benchmark_name, feature_name
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "feature", "num_models", "exp"),
        [
            ("existing", _empty_feature("bla", MockFeature()), 1, Failure(RunFeatureMissingError("existing", "bla"))),
            ("new", None, 1, Failure(RunModelsetMissingError("existing"))),
            ("existing", None, 1, Success(None)),
            ("existing", "existing", 1, Success(None)),
        ],
    )
    def test_run(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        feature: FeatureEntity | str | None,
        num_models: int,
        exp: Result[None, RunFeatureMissingError | RunModelsetMissingError],
    ) -> None:
        usecase.benchmark_create_uc()(benchmark_name="new")
        benchmark = usecase.benchmark_load_uc()(benchmark_name=benchmark_name).unwrap()

        if isinstance(feature, str):
            feature = next((f for f in benchmark.features if f.name == feature), None)

        result = usecase.benchmark_run_feature_uc()(benchmark=benchmark, feature=feature)

        assert type(result) is type(exp)

        benchmark = usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()
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
        usecase: UsecaseContainer,
        model: Model,
    ) -> None:
        # check if rerun changes the results

        assert is_successful(usecase.model_add_uc()("existing", model))

        assert is_successful(usecase.benchmark_set_modelset_uc()(benchmark_name="existing", modelset_name="existing"))

        benchmark: BenchmarkEntity = usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()

        assert benchmark.modelset is not None
        assert len(benchmark.modelset.models) > 0

        usecase.benchmark_run_feature_uc()(benchmark=benchmark, feature=None)

        for f in benchmark.features:
            for result in f.results.values():
                assert result.status is JobStatus.DONE

        usecase.benchmark_run_feature_uc()(benchmark=benchmark, feature=None)

        benchmark2 = usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()

        assert benchmark.features == benchmark2.features

    def test_run_failing_feature(
        self,
        usecase: UsecaseContainer,
        model: Model,
    ) -> None:
        assert is_successful(usecase.model_add_uc()("existing", model))

        assert is_successful(usecase.benchmark_set_modelset_uc()(benchmark_name="existing", modelset_name="existing"))
        usecase.benchmark_add_feature_uc()(
            benchmark_name="existing", name="failure", feature=MockFeatureFailing()
        ).unwrap()
        benchmark: BenchmarkEntity = usecase.benchmark_load_uc()(benchmark_name="existing").unwrap()

        feature = next((f for f in benchmark.features if f.name == "failure"), None)
        usecase.benchmark_run_feature_uc()(benchmark=benchmark, feature=feature)

        f = next((f for f in benchmark.features if f.name == "failure"), None)
        assert f is not None
        assert f.results["default_model"].status is JobStatus.FAILED
        assert f.results["default_model"].error == "Model failed."
