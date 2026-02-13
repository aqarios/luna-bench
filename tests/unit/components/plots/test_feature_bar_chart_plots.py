from unittest.mock import MagicMock, patch

from luna_bench.components.features.var_num_feature import VarNumberFeatureResult
from luna_bench.components.plots import VarNumberBarChartPlot
from luna_bench.components.plots.utils.dataframe_conversion import feature_to_dataframe
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.feature_result_entity import FeatureResultEntity

from .conftest import mock_var_entity, mock_var_validation_result


class TestFeatureToDataframe:
    def test_basic(self) -> None:
        entity = mock_var_entity(("m1", 10), ("m2", 20))
        df = feature_to_dataframe(entity, VarNumberFeatureResult, "var_number")
        assert len(df) == 2
        assert set(df.columns) == {"model", "var_number"}

    def test_with_value_accessor(self) -> None:
        entity = mock_var_entity(("m1", 10))
        df = feature_to_dataframe(
            entity, VarNumberFeatureResult, "custom_col", value_accessor=lambda r: r.var_number * 2
        )
        assert len(df) == 1
        assert df["custom_col"].iloc[0] == 20

    def test_skips_none_results(self) -> None:
        entity = mock_var_entity()
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
        data = mock_var_validation_result(("m1", 10), ("m2", 20))
        p.run(data)
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()

    @patch("luna_bench.components.plots.feature_plots.bar_chart_plots.sns")
    @patch("luna_bench.components.plots.feature_plots.bar_chart_plots.plt")
    def test_run_empty_data(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        p = VarNumberBarChartPlot()
        data = mock_var_validation_result()
        p.run(data)
        mock_sns.barplot.assert_not_called()
        mock_plt.show.assert_not_called()
