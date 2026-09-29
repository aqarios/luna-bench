from __future__ import annotations

import base64
from collections.abc import Sequence  # noqa: TC003 # A pydantic field annotation, resolved at runtime.
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
    (bytes) are encoded as base64 strings to stay JSON-compatible, and values
    JSON has no form for, such as a provider's own object in a run's metadata,
    are rendered as their string form.

    Attributes
    ----------
    indent : int | None
        Indentation width for pretty-printing; ``None`` for compact output.
        Defaults to ``None``.
    orient : JsonOrient
        JSON layout passed to ``DataFrame.to_json``. Defaults to ``"records"``.
    include_solution : bool
        Whether to include the serialized solution column. Defaults to False.
    drop : Sequence[str]
        Columns to leave out of the JSON, by their name in the exported table. Empty
        by default; see `DataFrameExporter.drop`.
    """

    indent: int | None = None
    orient: JsonOrient = "records"
    include_solution: bool = False
    drop: Sequence[str] = ()

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
        df = DataFrameExporter(include_solution=self.include_solution, drop=self.drop).export(benchmark_results)
        # A dropped solution column is nothing to encode, which is what asking for both
        # amounts to.
        if self.include_solution and "solution" in df.columns:
            df["solution"] = df["solution"].map(
                lambda value: base64.b64encode(value).decode("ascii") if isinstance(value, bytes) else value
            )
        # Metadata is whatever the solver reported, a provider's own objects included. Left to
        # itself pandas renders an object it does not recognise from its attributes, which for
        # many of them is an empty `{}`; its string form at least says what the value was.
        return df.to_json(orient=self.orient, indent=self.indent, default_handler=str)
