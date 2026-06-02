"""Output directory setup for benchmark runs."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from luna_quantum import Logging
from returns.result import Result, Success

from luna_bench._internal.usecases.benchmark.protocols import OutputDirSetupUc
from luna_bench.configs.config import config

if TYPE_CHECKING:
    from luna_bench.entities import BenchmarkEntity


class OutputDirSetupUcImpl(OutputDirSetupUc):
    """Set up the output directory for a benchmark run."""

    _logger = Logging.get_logger(__name__)

    def __call__(self, benchmark: BenchmarkEntity, root_folder: str | None = None) -> Result[None, str]:

        root = Path(root_folder or config.LB_OUTPUT_DIR).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)

        dir_output = Path(root, "benchmarks", benchmark.name)
        dir_output.mkdir(parents=True, exist_ok=True)

        benchmark.output_dir = str(dir_output)

        dir_plots = Path(dir_output, "plots")
        dir_plots.mkdir(parents=True, exist_ok=True)

        dir_logs = Path(dir_output, "logs")
        dir_logs.mkdir(parents=True, exist_ok=True)

        dir_import_models = Path(dir_output, "import_model")
        dir_import_models.mkdir(parents=True, exist_ok=True)

        benchmark.output_dir_plots = str(dir_plots)
        benchmark.output_dir_logs = str(dir_logs)
        benchmark.output_dir_import_models = str(dir_import_models)

        # Need to overwrite it here, otherwise the database paths will not be updated
        config.LB_OUTPUT_DIR = str(root)

        self._logger.info("Output root: %s → benchmarks/%s", root, benchmark.name)
        return Success(None)
