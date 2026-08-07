from abc import ABCMeta
from logging import Logger
from typing import TYPE_CHECKING, Any, ClassVar, dataclass_transform

from pydantic import BaseModel
from pydantic.fields import Field, PrivateAttr

from luna_bench.errors.write_once_error import WriteOnceError
from luna_bench.logging import BenchLogger

if TYPE_CHECKING:
    from pydantic._internal._model_construction import ModelMetaclass

    PydanticModelMetaclass = ModelMetaclass
else:
    PydanticModelMetaclass = type(BaseModel)


@dataclass_transform(kw_only_default=True, field_specifiers=(Field, PrivateAttr))
class WriteOnceMeta(PydanticModelMetaclass, ABCMeta):
    """
    Metaclass for write-once fields.

    Write once field must be written in the write_once_fields dict.
    Each field listed there will be protected from being overwritten/changed after the value is set onetime.

    Notes
    -----
    The `dataclass_transform` marker repeats what pydantic already declares on its own
    metaclass. Type checkers do not carry it through this subclass on their own, and
    without it every model built on this metaclass loses its generated ``__init__``:
    IDEs stop completing and start flagging field arguments such as
    ``AverageRuntimePlot(annotate=False)``.
    """

    _logger: ClassVar[Logger] = BenchLogger.get_logger(__name__)
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
                existing = namespace.get("__annotations__", {})
                try:
                    # For python 3.14+ we need to collect all pre-existing annotations.
                    # If the annotation lib doesn't exist,
                    # it means we are in python <3.14 and lazy loading doesn't exist.

                    from annotationlib import (  # type: ignore[import-not-found] # noqa: PLC0415
                        Format,
                        call_annotate_function,
                        get_annotate_from_class_namespace,
                    )

                    # Exactly one of the two branches below is reachable per interpreter, so
                    # neither can be covered by a single test run: on 3.14+ the import
                    # succeeds and the handler is dead, on <3.14 the reverse.
                    if annotate := get_annotate_from_class_namespace(namespace):  # pragma: no cover
                        existing = call_annotate_function(annotate, format=Format.FORWARDREF)
                except ImportError:  # pragma: no cover
                    pass

                namespace["__annotations__"] = {**existing, field_name: type_hint}

        return super().__new__(cls, name, bases, namespace, **kwargs)

    def __setattr__(cls, name: str, value: Any) -> None:  # noqa: ANN401
        """Overwrite setattr method of the metaclass from base models."""
        if name in cls.write_once_fields and name in cls.__dict__:
            raise WriteOnceError(class_name=cls.__name__, field_name=name)
        super().__setattr__(name, value)
