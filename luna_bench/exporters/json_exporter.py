from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Literal

from luna_bench.custom.base_components.base_exporter import BaseExporter
from luna_bench.exporters.dataframe_exporter import DataFrameExporter

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer

type JsonOrient = Literal["records", "columns", "index", "split", "table", "values"]


class JsonExporter(BaseExporter[str]):
    """Export benchmark results as a JSON string.

    Thin configuration layer over ``DataFrameExporter``: the merged results
    DataFrame is rendered with ``DataFrame.to_json``. Serialized solutions
    (bytes) are encoded as base64 strings to stay JSON-compatible.

    Attributes
    ----------
    indent : int | None
        Indentation width for pretty-printing; ``None`` for compact output.
        Defaults to ``None``.
    orient : JsonOrient
        JSON layout passed to ``DataFrame.to_json``. Defaults to ``"records"``.
    include_solution : bool
        Whether to include the serialized solution column. Defaults to False.
    """

    indent: int | None = None
    orient: JsonOrient = "records"
    include_solution: bool = False

    def export(self, benchmark_results: BenchmarkResultContainer) -> str:
        """Export benchmark results into a JSON string.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data to export.

        Returns
        -------
        str
            The results DataFrame rendered as JSON.
        """
        df = DataFrameExporter(include_solution=self.include_solution).export(benchmark_results)
        if self.include_solution:
            df["solution"] = df["solution"].map(
                lambda value: base64.b64encode(value).decode("ascii") if isinstance(value, bytes) else value
            )
        return df.to_json(orient=self.orient, indent=self.indent)
