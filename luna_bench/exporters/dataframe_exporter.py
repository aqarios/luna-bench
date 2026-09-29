from __future__ import annotations

from collections.abc import Sequence  # noqa: TC003 # A pydantic field annotation, resolved at runtime.
from typing import TYPE_CHECKING, Any

from luna_bench.custom.base_components.base_exporter import BaseExporter
from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.logging import BenchLogger

if TYPE_CHECKING:
    import pandas as pd

    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
    from luna_bench.custom.types import AlgorithmName, FeatureName, MetricName

#: What identifies a single run, and so what the algorithm and metric rows are joined on.
_RUN_KEY = ["algorithm", "model", "repetition"]

_logger = BenchLogger.get_logger(__name__)


class DataFrameExporter(BaseExporter["pd.DataFrame"]):
    """Export benchmark results as a single pandas DataFrame.

    Algorithm run results form the row spine (one row per ``(algorithm, model,
    repetition)``); metric results merge on those three and feature results merge on
    ``model``. Every result field becomes a ``"<name>/<field>"`` column.

    An algorithm added without ``repetitions`` contributes a single row per model, with
    ``repetition`` 0.

    Attributes
    ----------
    include_solution : bool
        Whether to include the serialized solution as a ``solution`` column.
        Defaults to False.
    drop : Sequence[str]
        Columns to leave out of the exported table, by their name in it -
        ``"metadata"``, ``"algorithm_config"``, or a result column such as
        ``"approx_ratio/approximation_ratio"``. Empty by default. A name that no
        column has is reported as a warning and otherwise ignored, so a metric that
        failed everywhere does not turn an export into an error.
    """

    include_solution: bool = False
    drop: Sequence[str] = ()

    def export(self, benchmark_results: BenchmarkResultContainer) -> pd.DataFrame:
        """Export benchmark results into a merged DataFrame.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data to export.

        Returns
        -------
        pd.DataFrame
            A DataFrame with columns ``algorithm``, ``model``, ``repetition``,
            ``metadata``, ``solution`` (optional), ``algorithm_config``, plus one
            column per result field of each metric and feature, less whatever
            :attr:`drop` names.

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

        merged = algorithms_df.merge(right=metrics_df, on=_RUN_KEY, how="left").merge(
            right=features_df, on="model", how="left"
        )
        return self._drop_columns(merged)

    def _drop_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return *df* without the columns :attr:`drop` names.

        Dropped at the end rather than left out while the parts are built, so a column
        the table is assembled on - ``model``, or a run's ``repetition`` - can be dropped
        from the output without the merges losing what they join on.

        Parameters
        ----------
        df : pd.DataFrame
            The merged table.

        Returns
        -------
        pd.DataFrame
            The table without those columns, or the table itself if none were named.
        """
        if not self.drop:
            return df

        unknown = [name for name in self.drop if name not in df.columns]
        if unknown:
            _logger.warning(
                f"Nothing to drop for {unknown}: the exported table has no such column. It holds {list(df.columns)}."
            )

        return df.drop(columns=[name for name in self.drop if name in df.columns])

    def _algorithms_to_dataframe(self, benchmark_results: BenchmarkResultContainer) -> pd.DataFrame:
        """Return one row per (algorithm, model, repetition), ordered algorithm-major."""
        import pandas as pd  # noqa: PLC0415

        algorithm_names: dict[AlgorithmName, None] = {}
        for _, algorithm_name, _ in benchmark_results.get_all_algorithms():
            algorithm_names.setdefault(algorithm_name)

        rows: list[dict[str, Any]] = []
        for algorithm_name in algorithm_names:
            for model_name, algo_results in benchmark_results.algorithms.items():
                for run_result in algo_results.get(algorithm_name, []):
                    row: dict[str, Any] = {
                        "algorithm": algorithm_name,
                        "model": model_name,
                        "repetition": run_result.repetition,
                        "metadata": run_result.metadata,
                    }
                    if self.include_solution:
                        row["solution"] = run_result.solution.serialize() if run_result.solution is not None else None
                    row["algorithm_config"] = run_result.algorithm.model_dump()
                    rows.append(row)
        return pd.DataFrame(rows)

    @staticmethod
    def _metrics_to_dataframe(benchmark_results: BenchmarkResultContainer) -> pd.DataFrame:
        """Return all metric results merged into a single DataFrame on ``(algorithm, model, repetition)``."""
        import pandas as pd  # noqa: PLC0415

        rows_by_name: dict[MetricName, list[dict[str, Any]]] = {}
        for model_name, algorithm_name, metric_results in benchmark_results.get_all_metrics():
            for results_by_name in metric_results.data.values():
                for metric_name, (metric_result, _config) in results_by_name.items():
                    row: dict[str, Any] = {
                        "algorithm": algorithm_name,
                        "model": model_name,
                        "repetition": metric_results.repetition,
                    }
                    for field_name, value in metric_result.model_dump().items():
                        row[f"{metric_name}/{field_name}"] = value
                    rows_by_name.setdefault(metric_name, []).append(row)

        # Typed rather than empty-and-untyped: pandas refuses to merge an object column
        # against the int64 the repetitions come out as.
        merged = pd.DataFrame(
            {"algorithm": pd.Series(dtype=str), "model": pd.Series(dtype=str), "repetition": pd.Series(dtype="int64")}
        )
        for rows in rows_by_name.values():
            merged = merged.merge(pd.DataFrame(rows), on=_RUN_KEY, how="outer")
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
