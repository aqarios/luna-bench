from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer

from .protocols import BenchmarkExportUc

if TYPE_CHECKING:
    from luna_bench.custom import Exporter
    from luna_bench.entities import BenchmarkEntity


class BenchmarkExportUcImpl(BenchmarkExportUc):
    """Export benchmark results by building a result container and delegating to an exporter."""

    def __call__[T](self, benchmark: BenchmarkEntity, exporter: Exporter[T]) -> T:
        """Build a result container from the benchmark and delegate to the exporter.

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark whose results to export.
        exporter : Exporter[T]
            The exporter strategy that converts results into the target format.

        Returns
        -------
        T
            The exported payload.
        """
        benchmark_result_container = BenchmarkResultContainer.from_benchmark(benchmark)
        return exporter.export(benchmark_result_container)
