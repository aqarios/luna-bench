from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from luna_bench.errors.components.metrics.metric_result_unknown_name_error import MetricResulUnknownNameError
from luna_bench.errors.components.metrics.metric_result_wrong_class_error import MetricResultWrongClassError
from luna_bench.types import MetricClass, MetricComputed, MetricName, MetricResult


class MetricResults(BaseModel):
    """Metric results container."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    allowed: list[MetricClass]

    data: Mapping[MetricClass, Mapping[MetricName, MetricComputed]]

    def get_all_with_config(self, metric_cls: MetricClass) -> Mapping[MetricName, MetricComputed]:
        """
        Get all results for a given metric class with their configurations.

        Parameters
        ----------
        metric_cls : MetricClass
            The metric class to retrieve results for.

        Returns
        -------
        Mapping[MetricName, MetricComputed]
            A mapping of metric names to their corresponding results and configurations.

        Raises
        ------
        MetricResultWrongClassError
            If the provided metric class is not allowed in this MetricResults instance.
        """
        if metric_cls not in self.allowed:
            raise MetricResultWrongClassError(metric_cls, self.allowed)
        return self.data.get(metric_cls, {})

    def get_all(self, metric_cls: MetricClass) -> Mapping[MetricName, MetricResult]:
        """
        Get all results for a given metric class.

        Parameters
        ----------
        metric_cls : MetricClass
            The metric class to retrieve results for.

        Returns
        -------
        Mapping[MetricName, MetricResult]
            A mapping of metric names to their corresponding results (without configurations).

        Raises
        ------
        MetricResultWrongClassError
            If the provided metric class is not allowed in this MetricResults instance.
        """
        return {name: result[0] for name, result in self.get_all_with_config(metric_cls).items()}

    def get(self, metric_cls: MetricClass, metric_name: MetricName) -> MetricResult:
        """
        Get a single result for a given metric class and name.

        Parameters
        ----------
        metric_cls : MetricClass
            The metric class to retrieve the result for.
        metric_name : MetricName
            The name of the metric to retrieve the result for.

        Returns
        -------
        MetricResult
            The result for the specified metric (without configuration).

        Raises
        ------
        MetricResultWrongClassError
            If the provided metric class is not allowed.
        MetricResulUnknownNameError
            If the provided metric name is not found for the given class.
        """
        return self.get_with_config(metric_cls=metric_cls, metric_name=metric_name)[0]

    def get_with_config(self, metric_cls: MetricClass, metric_name: MetricName) -> MetricComputed:
        """
        Get a single result with its configuration for a given metric class and name.

        Parameters
        ----------
        metric_cls : MetricClass
            The metric class to retrieve the result for.
        metric_name : MetricName
            The name of the metric to retrieve the result for.

        Returns
        -------
        MetricComputed
            The result and configuration for the specified metric.

        Raises
        ------
        MetricResultWrongClassError
            If the provided metric class is not allowed.
        MetricResulUnknownNameError
            If the provided metric name is not found for the given class.
        """
        if metric_cls not in self.allowed:
            raise MetricResultWrongClassError(metric_cls, self.allowed)
        if metric_name not in self.data[metric_cls]:
            raise MetricResulUnknownNameError(
                metric_class=metric_cls, metric_name=metric_name, known_names=list(self.data[metric_cls].keys())
            )

        return self.data[metric_cls][metric_name]

    def first(self, metric_cls: MetricClass) -> MetricResult:
        """
        Retrieve the first result for a given metric class.

        Parameters
        ----------
        metric_cls: MetricClass
            The class for which the first result should be retrieved.

        Returns
        -------
        MetricResult
            The first metric result for the given class (without configuration).

        Raises
        ------
        MetricResultWrongClassError
            If the provided metric class is not allowed.
        """
        return self.first_with_config(metric_cls=metric_cls)[0]

    def first_with_config(self, metric_cls: MetricClass) -> MetricComputed:
        """
        Retrieve the first result with its configuration for a given metric class.

        Parameters
        ----------
        metric_cls: MetricClass
            The class for which the first result should be retrieved.

        Returns
        -------
        MetricComputed
            A tuple containing the first metric result and its configuration for the given class.

        Raises
        ------
        MetricResultWrongClassError
            If the provided metric class is not allowed.
        """
        return next(iter(self.get_all_with_config(metric_cls).values()))
