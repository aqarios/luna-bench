from __future__ import annotations

from luna_bench._internal.user_models import FeatureUserModel


class Feature(FeatureUserModel):
    """User-facing feature class."""

    # TODO(Llewellyn): This can maybe be removed and FeatureUserModel renamed to Feature.  # noqa: FIX002

    def run(self) -> None: ...  # noqa: D102 # Not yet implemented

    def result(self) -> None: ...  # noqa: D102 # Not yet implemented

    def reset(self) -> None: ...  # noqa: D102 # Not yet implemented
