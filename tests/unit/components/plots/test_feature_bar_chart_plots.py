from unittest.mock import MagicMock, patch

from luna_bench.components.features.var_num_feature import VarNumberFeature, VarNumberFeatureResult
from luna_bench.components.plots import VarNumberBarChartPlot
from luna_bench.components.plots.generics.features_plot import FeaturesValidationResult
from luna_bench.components.plots.utils.dataframe_conversion import feature_to_dataframe
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.types import FeatureResult


def _var_entity(*values: tuple[str, int]) -> FeatureEntity:
    results = {}
    for model_name, var_num in values:
        results[model_name] = FeatureResultEntity(
            processing_time_ms=10,
            model_name=model_name,
            status=JobStatus.DONE,
            error=None,
            result=FeatureResult(**VarNumberFeatureResult(var_number=var_num).model_dump()),
        )
    return FeatureEntity(name="var_num", status=JobStatus.DONE, feature=VarNumberFeature(), results=results)


class TestFeatureToDataframe:
    def test_basic(self) -> None:
        entity = _var_entity(("m1", 10), ("m2", 20))
        df = feature_to_dataframe(entity, VarNumberFeatureResult, "var_number")
        assert len(df) == 2
        assert set(df.columns) == {"model", "var_number"}

    def test_with_value_accessor(self) -> None:
        entity = _var_entity(("m1", 10))
        df = feature_to_dataframe(
            entity, VarNumberFeatureResult, "custom_col", value_accessor=lambda r: r.var_number * 2
        )
        assert len(df) == 1
        assert df["custom_col"].iloc[0] == 20

    def test_skips_none_results(self) -> None:
        entity = _var_entity()
        entity.results["m1"] = FeatureResultEntity(
            processing_time_ms=0,
            model_name="m1",
            status=JobStatus.FAILED,
            error="err",
            result=None,
        )
        df = feature_to_dataframe(entity, VarNumberFeatureResult, "var_number")
        assert len(df) == 0


class TestVarNumberBarChartPlot:
    @patch("luna_bench.components.plots.feature_plots.bar_chart_plots.sns")
    @patch("luna_bench.components.plots.feature_plots.bar_chart_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        p = VarNumberBarChartPlot()
        data = FeaturesValidationResult(
            features={VarNumberFeature.registered_id: _var_entity(("m1", 10), ("m2", 20))},
        )
        p.run(data)
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()

    @patch("luna_bench.components.plots.feature_plots.bar_chart_plots.sns")
    @patch("luna_bench.components.plots.feature_plots.bar_chart_plots.plt")
    def test_run_empty_data(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        p = VarNumberBarChartPlot()
        entity = FeatureEntity(name="var_num", status=JobStatus.DONE, feature=VarNumberFeature(), results={})
        data = FeaturesValidationResult(features={VarNumberFeature.registered_id: entity})
        p.run(data)
        mock_sns.barplot.assert_not_called()
        mock_plt.show.assert_not_called()
