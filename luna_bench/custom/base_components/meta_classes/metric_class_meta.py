from typing import Any, ClassVar

from luna_bench.custom.base_components.base_feature import BaseFeature

from .registered_class_meta import RegisteredClassMeta


class MetricClassMeta(RegisteredClassMeta):
    """
    Metaclass for metric classes.

    Two fields are set to be 'write-once': registered_id and required_features.
    """

    write_once_fields: ClassVar[dict[str, Any]] = {
        "registered_id": ClassVar[str],
        "required_features": ClassVar[tuple[BaseFeature, ...] | None],
    }
