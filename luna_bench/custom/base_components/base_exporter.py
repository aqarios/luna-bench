from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


@runtime_checkable
class Exporter[T_co](Protocol):
    """Strategy interface for exporting benchmark results.

    Any object implementing ``export`` satisfies this protocol (structural
    typing), so custom export formats can be added without modifying the
    ``Benchmark`` class::

        benchmark.export(CsvExporter(delimiter=";"))

    ``T_co`` is the export payload type, e.g. ``str`` for CSV/JSON exporters,
    ``bytes`` for binary formats, or ``pd.DataFrame`` for the DataFrame
    exporter.
    """

    def export(self, benchmark_results: BenchmarkResultContainer) -> T_co:
        """Export benchmark results into the target format.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data (features, metrics, and algorithm run
            results) to export.

        Returns
        -------
        T_co
            The exported payload.
        """
        ...


class BaseExporter[T](BaseModel, ABC):
    """Abstract base class for exporters implementing the ``Exporter`` protocol.

    Subclassing is not required to satisfy ``Exporter`` (structural typing),
    but it makes the relationship explicit: IDEs and type checkers immediately
    flag subclasses that fall out of sync when the protocol changes. All
    built-in exporters extend this class.
    """

    @abstractmethod
    def export(self, benchmark_results: BenchmarkResultContainer) -> T:
        """Export benchmark results into the target format.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data (features, metrics, and algorithm run
            results) to export.

        Returns
        -------
        T
            The exported payload.
        """
