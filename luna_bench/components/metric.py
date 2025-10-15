from __future__ import annotations

from luna_bench._internal.user_models import MetricUserModel


class Metric(MetricUserModel):
    """User-facing metric class."""

    # TODO(Llewellyn): This can maybe be removed and MetricUserModel renamed to Metric.  # noqa: FIX002

    def run(self) -> None: ...  # noqa: D102 # Not yet implemented

    def result(self) -> None: ...  # noqa: D102 # Not yet implemented

    def reset(self) -> None: ...  # noqa: D102 # Not yet implemented
