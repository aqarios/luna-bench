from abc import ABCMeta
from logging import Logger
from typing import TYPE_CHECKING, Any, ClassVar

from luna_quantum import Logging
from pydantic import BaseModel

from luna_bench.errors.write_once_error import WriteOnceError

if TYPE_CHECKING:
    from pydantic._internal._model_construction import ModelMetaclass

    PydanticModelMetaclass = ModelMetaclass
else:
    PydanticModelMetaclass = type(BaseModel)


class WriteOnceMeta(PydanticModelMetaclass, ABCMeta):
    """
    Metaclass for write-once fields.

    Write once field must be written in the write_once_fields dict.
    Each field listed there will be protected from being overwritten/changed after the value is set onetime.
    """

    _logger: ClassVar[Logger] = Logging.get_logger(__name__)
    write_once_fields: ClassVar[dict[str, Any]] = {}

    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs: Any) -> type:
        """Overwrite a new method of the metaclass from base models."""
        for field_name, type_hint in cls.write_once_fields.items():
            if field_name in namespace:
                WriteOnceMeta._logger.warning(
                    f"{name}.{field_name} is already defined in the class body."
                    f"This field is intended to be a write-once field."
                )
            else:
                annotations: dict[str, Any] = namespace.setdefault("__annotations__", {})
                annotations.setdefault(field_name, type_hint)

        return super().__new__(cls, name, bases, namespace, **kwargs)

    def __setattr__(cls, name: str, value: Any) -> None:  # noqa: ANN401
        """Overwrite setattr method of the metaclass from base models."""
        if name in cls.write_once_fields and name in cls.__dict__:
            raise WriteOnceError(class_name=cls.__name__, field_name=name)
        super().__setattr__(name, value)
