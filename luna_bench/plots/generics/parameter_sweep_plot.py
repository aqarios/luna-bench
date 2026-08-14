"""Line plot of a metric against a parameter the algorithms were configured with."""

from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar

import pandas as pd

from luna_bench.errors.components.plots.plot_metric_undeclared_error import PlotMetricUndeclaredError
from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.plots.dimensions import Dimension, MetricDimension, ModelDimension, ParameterDimension
from luna_bench.plots.plot_style import ErrorBars
from luna_bench.plots.utils import AUTO_ERRORBAR, REFERENCE_LINE_COLOUR, Aggregation, ErrorBar, LunaColours

from .seaborn_plot import SeabornPlot

if TYPE_CHECKING:
    from logging import Logger

    from luna_bench.custom import BenchmarkResultContainer
    from luna_bench.custom.base_results.metric_result import MetricResult
    from luna_bench.custom.types import MetricClass


class ParameterSweepPlot(SeabornPlot, ABC):
    """Base of a plot that follows a metric as one algorithm parameter grows.

    A sweep runs the same algorithm several times with a single setting changed - the
    layer count of a QAOA, the number of shots, a time limit - and asks what that buys.
    This plot reads the setting off the *configuration* of each algorithm rather than
    off its results, so the benchmark only has to contain one algorithm entry per value:

    .. code-block:: python

        for layers in (1, 2, 3, 4):
            bench.add_algorithm(f"qaoa_p{layers}", QAOA(reps=layers))

        bench.add_plot("layers", ApproximationRatioVsParameterPlot(x=ParameterDimension("reps")))

    Both axes are dimensions, as they are on a bar plot: :attr:`x` says which setting is
    swept, :attr:`y` what is measured against it, and each titles its own axis. The x is a
    `ParameterDimension` specifically and not any dimension, since a sweep is read off the
    *distance* between its points - there is no sweeping over a model.

    Algorithms whose configuration has no such attribute are left out, which is what
    keeps a classical baseline in the same benchmark from breaking the sweep.

    Attributes
    ----------
    x : ParameterDimension
        The setting that is swept, e.g. ``ParameterDimension("reps")``. Also titles the
        axis.
    y : MetricDimension
        What the lines measure - the attribute read off each result, and its axis title.
    grouping : Dimension | None
        What is drawn as a line of its own: `ModelDimension` by default, or any other
        dimension - `AlgorithmDimension`, `FeatureDimension`, `ParameterDimension`.
        ``None`` draws a single line, aggregated over the models.
    marker : str
        Marker drawn at each sampled parameter value, by default ``"o"``.
    aggregation : Aggregation
        Aggregation applied when several rows share an x value, by default their mean.
    errorbars : ErrorBars
        The error band around each line.

    Requires
    --------
    Install the 'pre-defined' extra: ``pip install luna-bench[pre-defined]``

    See Also
    --------
    SeabornPlot : Figure size, output formats, and saving.
    """

    logger: ClassVar[Logger] = logging.getLogger(__name__)

    x: ParameterDimension = ParameterDimension("reps")
    """The setting that is swept: what the points are spaced by, and its title on the axis.

    Name the parameter as the algorithm does - ``"reps"``, ``"layers"``, ``"num_shots"``,
    ... An algorithm without that attribute contributes no points.
    """

    y: MetricDimension = MetricDimension("value")
    """What the lines measure: the attribute read off each result, and its axis title."""

    grouping: Dimension | None = ModelDimension()
    """What is drawn as a line of its own, by default one per model.

    Any of the dimensions - `ModelDimension`, `AlgorithmDimension`, `FeatureDimension`,
    `ParameterDimension` - or ``None``, which aggregates them into a single line.
    """

    marker: str = "o"
    """Marker drawn at each sampled parameter value, so single points stay visible."""

    aggregation: Aggregation = Aggregation.MEAN
    """Aggregation applied when several rows share an x value."""

    errorbars: ErrorBars | None = ErrorBars()
    """The error band around each line: what it shows. Its colour follows the line.

    ``None`` draws none, the same as ``ErrorBars(spec=None)``.
    """

    @property
    def metric_cls(self) -> MetricClass:
        """The metric this plot reads, taken from its ``@plot(...)`` declaration.

        Returns
        -------
        MetricClass
            The first declared metric class.

        Raises
        ------
        PlotMetricUndeclaredError
            If the plot declares no metric, so there is nothing to read.
        """
        if not self.required_metrics:
            raise PlotMetricUndeclaredError(type(self).__name__)
        return self.required_metrics[0]

    def value(self, metric_result: MetricResult) -> float:
        """Return the number a single metric result contributes.

        Parameters
        ----------
        metric_result : MetricResult
            One result of :attr:`metric_cls`.

        Returns
        -------
        float
            The value plotted for this result, by default the attribute :attr:`y` names.
        """
        return self.y.of(metric_result)

    def rows(self, benchmark_results: BenchmarkResultContainer) -> list[dict[str, Any]]:
        """Return one row per measurement, tagged with the run it came from.

        Which of them belong on the axis is :attr:`x`'s decision, so they are collected
        without asking - the model and the algorithm are what the dimensions look the rest
        up by.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data.

        Returns
        -------
        list[dict[str, Any]]
            Rows carrying the metric value, the model, and the algorithm.
        """
        return [
            {
                self.y.column: self.value(metric_result),
                "model": model_name,
                "algorithm": algorithm_name,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(self.metric_cls)
        ]

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
        """Resolve both dimensions onto the rows and draw what is left of them.

        The x is resolved first: it drops the algorithms that were never configured with
        the swept setting, and the grouping then only has to tell apart what remains.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data consumed by the plot implementation.
        save_dir : str | None, optional
            Directory to save the figure into, by default ``None``.
        """
        rows = self.rows(benchmark_results)

        if not rows or self.x.resolve_values(benchmark_results, rows) is None:
            self.logger.warning(
                "%s: no algorithm carries a numeric '%s', nothing to sweep over",
                self.__class__.__name__,
                self.x.parameter,
            )
            return

        self.create(rows=rows, save_dir=save_dir, **self.apply_grouping(benchmark_results, rows))

    def apply_grouping(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Split *rows* into a line each along :attr:`grouping`.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data the feature results and algorithm configurations are read from.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated in place.

        Returns
        -------
        dict[str, Any]
            Keyword arguments to forward to :meth:`create`. Empty when no grouping applies,
            so call sites can splat it unconditionally.
        """
        if self.grouping is None:
            return {}

        column = self.grouping.resolve(benchmark_results, rows)
        if column is None:
            self.logger.warning("%s: drawing a single line", type(self).__name__)
            return {}

        return {"hue": column}

    def create(self, *, rows: list[dict[str, Any]], save_dir: str | None = None, **kwargs: Any) -> None:
        """Draw the sweep as a line per group with a marker at every sampled value.

        The rows are expected to carry both axes already, under the titles the dimensions
        gave them; :meth:`run` is what puts them there.

        Parameters
        ----------
        rows : list[dict[str, Any]]
            Row-oriented plot data.
        save_dir : str | None, optional
            Directory to save the figure into, by default ``None``.
        **kwargs : Any
            Additional keyword arguments forwarded to :func:`seaborn.lineplot`, including
            the ``hue`` the grouping resolved to. They override the defaults computed here.
        """
        check_optional_dependency("matplotlib")
        check_optional_dependency("seaborn")
        import seaborn as sns  # noqa: PLC0415
        from matplotlib import pyplot as plt  # noqa: PLC0415

        df, missing = self.resolve_missing(pd.DataFrame(rows), self.y.column)
        if df.empty:
            self.logger.warning("%s: every value is missing or not finite, nothing to plot", type(self).__name__)
            return

        self.setup_figure()

        lineplot_kwargs: dict[str, Any] = {
            "data": df,
            "x": self.x.title,
            "y": self.y.column,
            "marker": self.marker,
            "estimator": self.aggregation.estimator,
            "errorbar": self._errorbar(),
        }
        lineplot_kwargs.update(self.figure.seaborn_kwargs)
        lineplot_kwargs.update(kwargs)
        lineplot_kwargs.update(self._color_kwargs(df, lineplot_kwargs.get("hue")))

        sns.lineplot(**lineplot_kwargs)

        if self.y.reference is not None:
            plt.axhline(
                y=self.y.reference, color=REFERENCE_LINE_COLOUR, linestyle="--", alpha=0.7, label=self.y.reference_label
            )
            if self.y.reference_label:
                plt.legend()

        handles, labels = plt.gca().get_legend_handles_labels()
        # A filled step of the sweep is drawn as an ordinary point on the line, and the
        # line has no slot to put a cross under: the count in the key is what says it.
        self.note_missing(handles, labels, missing)
        self.place_legend(plt.gca(), handles, labels)

        # The swept values are the points that were measured, so label exactly those
        # rather than whatever ticks matplotlib would spread over the range.
        plt.xticks(sorted(df[self.x.title].unique()))

        self.finalize_plot(
            self.x.title,
            self.y.title,
            self.figure.title,
            self.y.limits,
            x_rotation=0,
            save_dir=save_dir,
        )

    def _errorbar(self) -> ErrorBar:
        """Return what the band around each line shows, if anything.

        Returns
        -------
        ErrorBar
            The specification seaborn is given.
        """
        if self.errorbars is None:
            return None
        return self.aggregation.errorbar if self.errorbars.spec == AUTO_ERRORBAR else self.errorbars.spec

    def _color_kwargs(self, df: pd.DataFrame, hue: str | None) -> dict[str, Any]:
        """Return the seaborn colour arguments for the lines.

        Parameters
        ----------
        df : pd.DataFrame
            The data being drawn.
        hue : str | None
            The column the grouping resolved to, if any.

        Returns
        -------
        dict[str, Any]
            A palette wide enough for the groups, or the single colour one line is drawn in.
        """
        if hue is None or hue not in df.columns:
            return {"color": str(LunaColours.LUNA_SOLVE)}

        return {"palette": LunaColours.palette(df[hue].nunique())}
