"""Builder for feature result structures and lookup tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from luna_bench.base_components import BaseFeature  # noqa: TC001
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.types import (  # noqa: TC001
    FeatureClass,
    FeatureComputed,
    FeatureName,
    FeatureResult,
    ModelName,
)

if TYPE_CHECKING:
    from luna_bench.entities import BenchmarkEntity


class FeatureResultBuilder:
    """Builder for feature result structures from a benchmark."""

    def __init__(self, benchmark: BenchmarkEntity) -> None:
        """
        Initialize the builder with a benchmark.

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark containing features and their results.
        """
        self.benchmark = benchmark
        self._lookup_map = self._build_lookup_map()

    def _build_lookup_map(
        self,
    ) -> dict[tuple[FeatureClass, ModelName], dict[FeatureName, FeatureComputed]]:
        """
        Build a lookup table of feature results by (type, model) for efficient access.

        Returns
        -------
        dict[tuple[FeatureClass, ModelName], dict[FeatureName, FeatureComputed]]
            Nested dict indexed by (feature_class, model_name) containing feature results.
        """
        feature_map: dict[tuple[FeatureClass, ModelName], dict[FeatureName, FeatureComputed]] = {}
        for f in self.benchmark.features:
            feature_type: FeatureClass = type(f.feature)
            feature_config: BaseFeature = f.feature
            for f_model_name, result in f.results.items():
                r: FeatureResult | None = result.result
                if r is not None:
                    feature_map.setdefault((feature_type, f_model_name), {})[f.name] = (r, feature_config)

        return feature_map

    def results(
        self,
        model_name: ModelName,
        required_features: list[FeatureClass],
    ) -> Result[FeatureResults, RunFeatureMissingError]:
        """
        Build and validate feature results for a metric and model.

        Parameters
        ----------
        model_name : ModelName
            The model name to retrieve features for.
        metric : MetricEntity
            The metric requiring specific features.

        Returns
        -------
        Result[FeatureResults, RunFeatureMissingError]
            Success with FeatureResults if all required features are available,
            Failure with RunFeatureMissingError if any required feature is missing.
        """
        feature_data: dict[FeatureClass, dict[FeatureName, FeatureComputed]] = {}

        for f in required_features:
            key: tuple[FeatureClass, ModelName] = (f, model_name)
            if key not in self._lookup_map:
                return Failure(RunFeatureMissingError(f.__name__, self.benchmark.name))
            feature_data[f] = self._lookup_map[key].copy()

        return Success(
            FeatureResults.model_construct(
                data=feature_data,
                allowed=required_features.copy(),
            )
        )
