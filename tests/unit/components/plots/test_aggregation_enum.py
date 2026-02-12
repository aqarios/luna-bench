from luna_bench.components.plots.utils.aggregation_enum import Aggregation


class TestAggregation:
    def test_mean_sd_estimator(self) -> None:
        assert Aggregation.MEAN_SD.estimator == "mean"

    def test_mean_sd_errorbar(self) -> None:
        assert Aggregation.MEAN_SD.errorbar == "sd"

    def test_mean_estimator(self) -> None:
        assert Aggregation.MEAN.estimator == "mean"

    def test_mean_errorbar(self) -> None:
        assert Aggregation.MEAN.errorbar is None

    def test_max_estimator(self) -> None:
        assert Aggregation.MAX.estimator == "max"

    def test_max_errorbar(self) -> None:
        assert Aggregation.MAX.errorbar is None

    def test_min_estimator(self) -> None:
        assert Aggregation.MIN.estimator == "min"

    def test_min_errorbar(self) -> None:
        assert Aggregation.MIN.errorbar is None
