"""Data directory setup for benchmark runs."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from luna_quantum import Logging
from returns.result import Result, Success

from luna_bench._internal.usecases.benchmark.protocols import DataDirSetupUc
from luna_bench.configs.config import config

if TYPE_CHECKING:
    from luna_bench.entities import BenchmarkEntity


class DataDirSetupUcImpl(DataDirSetupUc):
    """Set up the data_dir directory for a benchmark run."""

    _logger = Logging.get_logger(__name__)

    def __call__(self, benchmark: BenchmarkEntity, root_folder: str | None = None) -> Result[None, str]:

        root = Path(root_folder or config.LB_DATA_DIR).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)

        dir_data = Path(root, "benchmarks", benchmark.name)
        dir_data.mkdir(parents=True, exist_ok=True)

        benchmark.data_dir = str(dir_data)

        dir_plots = Path(dir_data, "plots")
        dir_plots.mkdir(parents=True, exist_ok=True)

        dir_logs = Path(dir_data, "logs")
        dir_logs.mkdir(parents=True, exist_ok=True)

        benchmark.data_dir_plots = str(dir_plots)
        benchmark.data_dir_logs = str(dir_logs)

        # Need to overwrite it here, otherwise the database paths will not be updated
        config.LB_DATA_DIR = str(root)

        self._logger.info("Data dir root: %s → benchmarks/%s", root, benchmark.name)
        return Success(None)
