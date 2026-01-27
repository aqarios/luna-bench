from typing import Any, ClassVar

from luna_bench.base_components.meta_classes.write_once_meta import WriteOnceMeta


class RegisteredClassMeta(WriteOnceMeta):
    """
    Metaclass for registered classes.

    Only the registered_id field is set to be a 'write-once' field.
    """

    write_once_fields: ClassVar[dict[str, Any]] = {"registered_id": ClassVar[str]}
