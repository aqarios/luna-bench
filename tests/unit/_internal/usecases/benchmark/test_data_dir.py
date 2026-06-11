from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from returns.result import Success

from luna_bench._internal.usecases.benchmark.data_dir import DataDirSetupUcImpl
from luna_bench.configs.config import config
from luna_bench.entities import BenchmarkEntity

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture()
def tmp_data_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture()
def entity() -> BenchmarkEntity:
    return BenchmarkEntity(
        name="test_benchmark",
        modelset=None,
        features=[],
        metrics=[],
        algorithms=[],
        plots=[],
    )


class TestDataDirSetupUc:
    """Test the DataDirSetupUcImpl use case."""

    @staticmethod
    def _run(uc: DataDirSetupUcImpl, entity: BenchmarkEntity, root: Path) -> None:
        result = uc(entity, root_folder=str(root))
        assert isinstance(result, Success)

    def test_creates_root_when_missing(self, entity: BenchmarkEntity, tmp_data_dir: Path) -> None:
        root = tmp_data_dir / "nonexistent"
        self._run(DataDirSetupUcImpl(), entity, root)
        assert root.exists()

    @pytest.mark.parametrize(
        "subdir",
        [
            "plots",
            "logs",
            "import_model",
        ],
    )
    def test_creates_subdirs(self, entity: BenchmarkEntity, tmp_data_dir: Path, subdir: str) -> None:
        self._run(DataDirSetupUcImpl(), entity, tmp_data_dir)
        assert (tmp_data_dir / "benchmarks" / entity.name / subdir).exists()

    @pytest.mark.parametrize(
        ("field", "subfolder"),
        [
            ("data_dir", ""),
            ("data_dir_plots", "plots"),
            ("data_dir_logs", "logs"),
            ("data_dir_import_models", "import_model"),
        ],
    )
    def test_sets_field(self, entity: BenchmarkEntity, tmp_data_dir: Path, field: str, subfolder: str) -> None:
        self._run(DataDirSetupUcImpl(), entity, tmp_data_dir)

        expected = str(tmp_data_dir / "benchmarks" / entity.name / subfolder)
        assert getattr(entity, field) == expected

    def test_updates_config_data_dir(self, entity: BenchmarkEntity, tmp_data_dir: Path) -> None:
        original = config.LB_DATA_DIR
        try:
            self._run(DataDirSetupUcImpl(), entity, tmp_data_dir)
            assert str(tmp_data_dir.resolve()) == config.LB_DATA_DIR
        finally:
            config.LB_DATA_DIR = original

    def test_falls_back_to_config_when_no_root_folder(self, entity: BenchmarkEntity, tmp_data_dir: Path) -> None:
        original = config.LB_DATA_DIR
        try:
            config.LB_DATA_DIR = str(tmp_data_dir / "from_config")
            result = DataDirSetupUcImpl()(entity)

            assert isinstance(result, Success)
            assert (tmp_data_dir / "from_config" / "benchmarks" / entity.name).exists()
        finally:
            config.LB_DATA_DIR = original
