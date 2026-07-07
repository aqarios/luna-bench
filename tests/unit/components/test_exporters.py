from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING

import pandas as pd
import pytest

from luna_bench._internal.usecases.benchmark.helper.benchmark_result_container_builder import (
    BenchmarkResultContainerBuilder,
)
from luna_bench.custom import BenchmarkResultContainer, Exporter
from luna_bench.entities import (
    AlgorithmEntity,
    AlgorithmResultEntity,
    BenchmarkEntity,
    FeatureEntity,
    JobStatus,
    MetricEntity,
)
from luna_bench.exporters import CsvExporter, DataFrameExporter, JsonExporter
from tests.unit.fixtures.mock_components import MockAlgorithm
from tests.unit.fixtures.mock_entities import make_algo_entity, make_feature_entity, make_metric_entity

if TYPE_CHECKING:
    from luna_model import Solution


def _make_container(
    features: list[FeatureEntity] | None = None,
    metrics: list[MetricEntity] | None = None,
    algorithms: list[AlgorithmEntity] | None = None,
) -> BenchmarkResultContainer:
    benchmark = BenchmarkEntity(
        name="test_bench",
        modelset=None,
        features=features or [],
        algorithms=algorithms or [],
        metrics=metrics or [],
        plots=[],
    )
    return BenchmarkResultContainerBuilder(benchmark).build()


def _default_container() -> BenchmarkResultContainer:
    return _make_container(
        features=[make_feature_entity("num_vars", ("model1", {"count": 42}))],
        metrics=[make_metric_entity("accuracy", ("algo1", "model1", {"score": 0.95}))],
        algorithms=[make_algo_entity("algo1", ["model1"])],
    )


class TestExporterProtocol:
    def test_builtin_exporters_satisfy_protocol(self) -> None:
        assert isinstance(DataFrameExporter(), Exporter)
        assert isinstance(CsvExporter(), Exporter)
        assert isinstance(JsonExporter(), Exporter)

    def test_custom_exporter_satisfies_protocol(self) -> None:
        class RowCountExporter:
            def export(self, benchmark_results: BenchmarkResultContainer) -> int:
                return len(list(benchmark_results.get_all_algorithms()))

        assert isinstance(RowCountExporter(), Exporter)
        assert RowCountExporter().export(_default_container()) == 1


class TestDataFrameExporter:
    def test_empty_container_raises_error(self) -> None:
        with pytest.raises(ValueError, match="no algorithm results available"):
            DataFrameExporter().export(_make_container())

    def test_merges_algorithms_metrics_and_features(self) -> None:
        df = DataFrameExporter().export(_default_container())

        expected_columns = ["algorithm", "model", "meta_data", "algorithm_config", "accuracy/score", "num_vars/count"]
        assert len(df) == 1
        assert list(df.columns) == expected_columns
        assert df.iloc[0]["algorithm"] == "algo1"
        assert df.iloc[0]["model"] == "model1"
        assert df.iloc[0]["accuracy/score"] == 0.95
        assert df.iloc[0]["num_vars/count"] == 42

    def test_missing_metric_result_is_na(self) -> None:
        container = _make_container(
            metrics=[make_metric_entity("accuracy", ("algo1", "model1", {"score": 0.95}))],
            algorithms=[make_algo_entity("algo1", ["model1"]), make_algo_entity("algo2", ["model1"])],
        )
        df = DataFrameExporter().export(container)

        assert len(df) == 2
        assert df.iloc[0]["accuracy/score"] == 0.95
        assert pd.isna(df.iloc[1]["accuracy/score"])

    def test_rows_are_algorithm_major(self) -> None:
        container = _make_container(
            algorithms=[
                make_algo_entity("algo1", ["model1", "model2"]),
                make_algo_entity("algo2", ["model1", "model2"]),
            ],
        )
        df = DataFrameExporter().export(container)

        assert list(zip(df["algorithm"], df["model"], strict=True)) == [
            ("algo1", "model1"),
            ("algo1", "model2"),
            ("algo2", "model1"),
            ("algo2", "model2"),
        ]

    def test_algorithm_without_result_for_model_has_no_row(self) -> None:
        container = _make_container(
            algorithms=[
                make_algo_entity("algo1", ["model1", "model2"]),
                make_algo_entity("algo2", ["model1"]),
            ],
        )
        df = DataFrameExporter().export(container)

        assert list(zip(df["algorithm"], df["model"], strict=True)) == [
            ("algo1", "model1"),
            ("algo1", "model2"),
            ("algo2", "model1"),
        ]

    def test_solution_excluded_by_default(self) -> None:
        df = DataFrameExporter().export(_default_container())

        assert "solution" not in df.columns

    def test_solution_included_and_serialized(self, solution: Solution) -> None:
        algo = AlgorithmEntity(
            name="algo1",
            algorithm=MockAlgorithm(),
            results={
                "model1": AlgorithmResultEntity(
                    meta_data=None,
                    status=JobStatus.DONE,
                    error=None,
                    solution=solution,
                    task_id=None,
                    retrival_data=None,
                    model_id=1,
                )
            },
        )
        df = DataFrameExporter(include_solution=True).export(_make_container(algorithms=[algo]))

        assert list(df.columns) == ["algorithm", "model", "meta_data", "solution", "algorithm_config"]
        assert df.iloc[0]["solution"] == solution.serialize()

    def test_algorithm_config_is_dumped(self) -> None:
        df = DataFrameExporter().export(_default_container())

        assert df.iloc[0]["algorithm_config"] == MockAlgorithm().model_dump()


class TestCsvExporter:
    def test_default_csv(self) -> None:
        csv_str = CsvExporter().export(_default_container())
        header, row = csv_str.strip().split("\n")

        assert header == "algorithm,model,meta_data,algorithm_config,accuracy/score,num_vars/count"
        assert row.startswith("algo1,model1,")

    def test_custom_delimiter(self) -> None:
        csv_str = CsvExporter(delimiter=";").export(_default_container())

        assert csv_str.startswith("algorithm;model;")

    def test_quoting_all(self) -> None:
        csv_str = CsvExporter(quoting="all").export(_default_container())

        assert csv_str.startswith('"algorithm","model",')

    def test_empty_container_raises_error(self) -> None:
        with pytest.raises(ValueError, match="no algorithm results available"):
            CsvExporter().export(_make_container())


class TestJsonExporter:
    def test_default_records_orient(self) -> None:
        json_str = JsonExporter().export(_default_container())
        records = json.loads(json_str)

        assert len(records) == 1
        assert records[0]["algorithm"] == "algo1"
        assert records[0]["model"] == "model1"
        assert records[0]["accuracy/score"] == 0.95
        assert records[0]["num_vars/count"] == 42

    def test_missing_result_is_null(self) -> None:
        container = _make_container(
            metrics=[make_metric_entity("accuracy", ("algo1", "model1", {"score": 0.95}))],
            algorithms=[make_algo_entity("algo1", ["model1"]), make_algo_entity("algo2", ["model1"])],
        )
        records = json.loads(JsonExporter().export(container))

        assert records[1]["accuracy/score"] is None

    def test_columns_orient(self) -> None:
        json_str = JsonExporter(orient="columns").export(_default_container())
        data = json.loads(json_str)

        assert data["algorithm"] == {"0": "algo1"}

    def test_indent(self) -> None:
        json_str = JsonExporter(indent=2).export(_default_container())

        assert "\n" in json_str

    def test_solution_is_base64_encoded(self, solution: Solution) -> None:
        algo = AlgorithmEntity(
            name="algo1",
            algorithm=MockAlgorithm(),
            results={
                "model1": AlgorithmResultEntity(
                    meta_data=None,
                    status=JobStatus.DONE,
                    error=None,
                    solution=solution,
                    task_id=None,
                    retrival_data=None,
                    model_id=1,
                )
            },
        )
        records = json.loads(JsonExporter(include_solution=True).export(_make_container(algorithms=[algo])))

        assert base64.b64decode(records[0]["solution"]) == solution.serialize()

    def test_empty_container_raises_error(self) -> None:
        with pytest.raises(ValueError, match="no algorithm results available"):
            JsonExporter().export(_make_container())
