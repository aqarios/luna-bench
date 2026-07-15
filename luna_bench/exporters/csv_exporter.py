from __future__ import annotations

import base64
import csv
from typing import TYPE_CHECKING, Literal

from luna_bench.custom.base_components.base_exporter import BaseExporter
from luna_bench.exporters.dataframe_exporter import DataFrameExporter

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer

type CsvQuoting = Literal["minimal", "all", "nonnumeric", "none"]

_QUOTING_MAP: dict[CsvQuoting, Literal[0, 1, 2, 3]] = {
    "minimal": csv.QUOTE_MINIMAL,
    "all": csv.QUOTE_ALL,
    "nonnumeric": csv.QUOTE_NONNUMERIC,
    "none": csv.QUOTE_NONE,
}


class CsvExporter(BaseExporter[str]):
    """Export benchmark results as a CSV string.

    Thin configuration layer over ``DataFrameExporter``: the merged results
    DataFrame is rendered with ``DataFrame.to_csv``. Serialized solutions
    (bytes) are encoded as base64 strings to stay CSV-compatible.

    Attributes
    ----------
    delimiter : str
        Field delimiter. Defaults to ``","``.
    quoting : CsvQuoting
        Quoting style, one of ``"minimal"``, ``"all"``, ``"nonnumeric"``, or
        ``"none"`` (mapped to the ``csv.QUOTE_*`` constants). Defaults to
        ``"minimal"``.
    include_solution : bool
        Whether to include the serialized solution column. Defaults to False.
    """

    delimiter: str = ","
    quoting: CsvQuoting = "minimal"
    include_solution: bool = False

    def export(self, benchmark_results: BenchmarkResultContainer) -> str:
        """Export benchmark results into a CSV string.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data to export.

        Returns
        -------
        str
            The results DataFrame rendered as CSV (without index column).
        """
        df = DataFrameExporter(include_solution=self.include_solution).export(benchmark_results)
        if self.include_solution:
            df["solution"] = df["solution"].map(
                lambda value: base64.b64encode(value).decode("ascii") if isinstance(value, bytes) else value
            )
        return df.to_csv(sep=self.delimiter, quoting=_QUOTING_MAP[self.quoting], index=False)
