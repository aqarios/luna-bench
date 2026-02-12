from playhouse.sqlite_udf import aggregate

from luna_bench.components.plots.utils.aggregation_enum import Aggregation
import pytest


class TestAggregation:
    @pytest.mark.parametrize(
        ("aggregation", "estimator", "errorbar"),[
            (Aggregation.MEAN_SD, "mean", "sd"),
            (Aggregation.MEAN, "mean", None),
            (Aggregation.MAX, "max", None),
            (Aggregation.MIN, "min", None),
        ],
    )
    def test_estimator_errorbar(self, aggregation: Aggregation, estimator: str | None, errorbar: str | None) -> None:
        assert aggregation.estimator == estimator
        assert aggregation.errorbar == errorbar
