from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom.base_components.base_exporter import BaseExporter
from luna_bench.helpers.optional_dependencies import check_optional_dependency

if TYPE_CHECKING:
    import pandas as pd

    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
    from luna_bench.custom.types import AlgorithmName, FeatureName, MetricName


class DataFrameExporter(BaseExporter["pd.DataFrame"]):
    """Export benchmark results as a single pandas DataFrame.

    Algorithm run results form the row spine (one row per ``(algorithm, model)``
    pair); metric results merge on ``(algorithm, model)`` and feature results
    merge on ``model``. Every result field becomes a ``"<name>/<field>"`` column.

    Attributes
    ----------
    include_solution : bool
        Whether to include the serialized solution as a ``solution`` column.
        Defaults to False.
    """

    include_solution: bool = False

    def export(self, benchmark_results: BenchmarkResultContainer) -> pd.DataFrame:
        """Export benchmark results into a merged DataFrame.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data to export.

        Returns
        -------
        pd.DataFrame
            A DataFrame with columns ``algorithm``, ``model``, ``meta_data``,
            ``solution`` (optional), ``algorithm_config``, plus one column per
            result field of each metric and feature.

        Raises
        ------
        ValueError
            If the container holds no algorithm results.
        """
        check_optional_dependency("pandas")
        if not benchmark_results.algorithms:
            msg = "Cannot build results DataFrame: no algorithm results available."
            raise ValueError(msg)

        algorithms_df = self._algorithms_to_dataframe(benchmark_results)
        metrics_df = self._metrics_to_dataframe(benchmark_results)
        features_df = self._features_to_dataframe(benchmark_results)

        return algorithms_df.merge(right=metrics_df, on=["algorithm", "model"], how="left").merge(
            right=features_df, on="model", how="left"
        )

    def _algorithms_to_dataframe(self, benchmark_results: BenchmarkResultContainer) -> pd.DataFrame:
        """Return one row per (algorithm, model) pair, ordered algorithm-major."""
        import pandas as pd  # noqa: PLC0415

        algorithm_names: dict[AlgorithmName, None] = {}
        for _, algorithm_name, _ in benchmark_results.get_all_algorithms():
            algorithm_names.setdefault(algorithm_name)

        rows: list[dict[str, Any]] = []
        for algorithm_name in algorithm_names:
            for model_name, algo_results in benchmark_results.algorithms.items():
                run_result = algo_results.get(algorithm_name)
                if run_result is None:
                    continue
                row: dict[str, Any] = {
                    "algorithm": algorithm_name,
                    "model": model_name,
                    "meta_data": run_result.meta_data,
                }
                if self.include_solution:
                    row["solution"] = run_result.solution.serialize() if run_result.solution is not None else None
                row["algorithm_config"] = run_result.algorithm.model_dump()
                rows.append(row)
        return pd.DataFrame(rows)

    @staticmethod
    def _metrics_to_dataframe(benchmark_results: BenchmarkResultContainer) -> pd.DataFrame:
        """Return all metric results merged into a single DataFrame on ``(algorithm, model)``."""
        import pandas as pd  # noqa: PLC0415

        rows_by_name: dict[MetricName, list[dict[str, Any]]] = {}
        for model_name, algorithm_name, metric_results in benchmark_results.get_all_metrics():
            for results_by_name in metric_results.data.values():
                for metric_name, (metric_result, _config) in results_by_name.items():
                    row: dict[str, Any] = {"algorithm": algorithm_name, "model": model_name}
                    for field_name, value in metric_result.model_dump().items():
                        row[f"{metric_name}/{field_name}"] = value
                    rows_by_name.setdefault(metric_name, []).append(row)

        merged = pd.DataFrame(columns=["algorithm", "model"])
        for rows in rows_by_name.values():
            merged = merged.merge(pd.DataFrame(rows), on=["algorithm", "model"], how="outer")
        return merged

    @staticmethod
    def _features_to_dataframe(benchmark_results: BenchmarkResultContainer) -> pd.DataFrame:
        """Return all feature results merged into a single DataFrame on ``model``."""
        import pandas as pd  # noqa: PLC0415

        rows_by_name: dict[FeatureName, list[dict[str, Any]]] = {}
        for model_name, feature_results in benchmark_results.features.items():
            for results_by_name in feature_results.data.values():
                for feature_name, (feature_result, _config) in results_by_name.items():
                    row: dict[str, Any] = {"model": model_name}
                    for field_name, value in feature_result.model_dump().items():
                        row[f"{feature_name}/{field_name}"] = value
                    rows_by_name.setdefault(feature_name, []).append(row)

        merged = pd.DataFrame(columns=["model"])
        for rows in rows_by_name.values():
            merged = merged.merge(pd.DataFrame(rows), on="model", how="outer")
        return merged
