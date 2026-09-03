"""Tests for grouping a plot by the axis a grid of algorithm variants varied."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import TypeAdapter

from luna_bench.algorithms.variants import AlgorithmGrid
from luna_bench.plots import ApproximationRatioPlot
from luna_bench.plots.dimensions import Dimension, GridDimension


def rows(*algorithms: str) -> list[dict[str, Any]]:
    """Return one plot row per algorithm name."""
    return [{"algorithm": name, "value": 1.0} for name in algorithms]


class TestGridDimension:
    def test_tags_each_row_with_the_label_of_its_algorithm(self) -> None:
        dimension = GridDimension(labels={"a[reps=2]": "2", "a[reps=4]": "4"}, label="reps")
        data = rows("a[reps=2]", "a[reps=4]")

        column = dimension.resolve(MagicMock(), data)

        assert column == "reps"
        assert [row["reps"] for row in data] == ["2", "4"]

    def test_an_algorithm_outside_the_grid_is_left_out_rather_than_pooled(self) -> None:
        """Pooling a baseline with the grid would put a mean of unrelated runs on the axis."""
        dimension = GridDimension(labels={"a[reps=2]": "2"}, label="reps")
        data = rows("a[reps=2]", "scip", "handpicked[reps=6]")

        dimension.resolve(MagicMock(), data)

        assert [row["algorithm"] for row in data] == ["a[reps=2]"]
        assert [row["reps"] for row in data] == ["2"]

    def test_the_surviving_rows_keep_the_order_they_arrived_in(self) -> None:
        dimension = GridDimension(labels={"a[reps=2]": "2", "a[reps=4]": "4"}, label="reps")
        data = rows("a[reps=4]", "scip", "a[reps=2]")

        dimension.resolve(MagicMock(), data)

        assert [row["reps"] for row in data] == ["4", "2"]

    def test_says_it_does_not_apply_when_no_row_is_in_the_grid(self) -> None:
        dimension = GridDimension(labels={"a[reps=2]": "2"}, label="reps")

        assert dimension.resolve(MagicMock(), rows("scip", "gurobi")) is None

    def test_the_axis_name_titles_the_column_by_default(self) -> None:
        dimension = GridDimension(labels={"a": "x"}, label="pipeline.xy_mixer.enable")

        assert dimension.title == "pipeline.xy_mixer.enable"

    def test_round_trips_through_the_dimension_union_as_stored_plot_config(self) -> None:
        """Plot configuration is persisted with the benchmark, so a dimension must survive JSON."""
        dimension = GridDimension(labels={"a[reps=2]": "2"}, label="reps")
        adapter = TypeAdapter(Dimension)

        restored = adapter.validate_json(adapter.dump_json(dimension))

        assert isinstance(restored, GridDimension)
        assert restored.labels == {"a[reps=2]": "2"}
        assert restored.title == "reps"

    def test_serves_as_both_the_bars_and_the_grouping_of_a_plot(self) -> None:
        dimension = GridDimension(labels={"a[reps=2]": "2"}, label="reps")

        plot = ApproximationRatioPlot(x=dimension, grouping=dimension)

        assert plot.x is dimension
        assert plot.grouping is dimension


class TestAlgorithmGridAxis:
    def test_returns_the_axis_as_a_dimension_labelled_by_its_values(self) -> None:
        grid = AlgorithmGrid(entities=[], axes={"reps": {"a[reps=2]": 2, "a[reps=4]": 4}})

        dimension = grid.axis("reps")

        assert dimension.labels == {"a[reps=2]": "2", "a[reps=4]": "4"}
        assert dimension.title == "reps"

    def test_display_labels_replace_the_raw_values(self) -> None:
        xy = "pipeline.xy_mixer.enable"
        grid = AlgorithmGrid(entities=[], axes={xy: {"a[f]": False, "a[t]": True}})

        dimension = grid.axis(xy, labels={False: "plain QAOA", True: "XY mixer"})

        assert dimension.labels == {"a[f]": "plain QAOA", "a[t]": "XY mixer"}

    def test_an_axis_that_was_not_varied_is_rejected(self) -> None:
        grid = AlgorithmGrid(entities=[], axes={"reps": {"a": 2}})

        with pytest.raises(KeyError, match="shots"):
            grid.axis("shots")


def test_the_axis_title_can_be_given_positionally_like_the_other_dimensions() -> None:
    dimension = GridDimension("Pipeline", labels={"a": "XY mixer"})

    assert dimension.title == "Pipeline"


class TestAlgorithmGridAxisTitle:
    """A dotted path is a fine axis name and a poor axis label."""

    def test_the_axis_title_defaults_to_the_axis_name(self) -> None:
        grid = AlgorithmGrid(entities=[], axes={"reps": {"a": 2}})

        assert grid.axis("reps").title == "reps"

    def test_a_title_replaces_the_dotted_path_on_the_figure(self) -> None:
        xy = "pipeline.xy_mixer.enable"
        grid = AlgorithmGrid(entities=[], axes={xy: {"a": True}})

        dimension = grid.axis(xy, labels={True: "XY mixer"}, title="Pipeline")

        assert dimension.title == "Pipeline"
        assert dimension.labels == {"a": "XY mixer"}
