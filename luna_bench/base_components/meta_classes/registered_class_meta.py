from typing import Any, ClassVar

from luna_quantum import Logging
from pydantic import BaseModel


class RegisteredClassMeta(type(BaseModel)):
    logger = Logging.get_logger(__name__)

    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs: Any):
        # Warn if the subclass explicitly defines registered_id in the class body.
        # (You can flip this logic if you only want to warn on "non-None" etc.)
        if "registered_id" in namespace:
            RegisteredClassMeta.logger.warning(
                f"{name}.registered_id is already defined in the class body; "
                f"the metaclass would normally inject a default. Keeping the provided value.",
            )
        else:
            ann = ClassVar[str | None]
            annotations: dict[str, Any] = namespace.setdefault("__annotations__", {})
            annotations.setdefault("registered_id", ann)

        return super().__new__(mcls, name, bases, namespace, **kwargs)

    def __setattr__(cls, name: str, value: Any) -> None:
        if name == "registered_id" and "registered_id" in cls.__dict__:
            raise AttributeError(f"{cls.__name__}.registered_id is write-once and cannot be changed.")
        super().__setattr__(name, value)

    def __getattribute__(cls, name: str) -> Any:
        if name == "registered_id" and name not in cls.__dict__:
            RegisteredClassMeta.logger.warning(
                f"{cls.__name__}.{name} was accessed but the class is not registered."
                f"Setting the value to an empty string."
            )
            cls.registered_id = ""
        return super().__getattribute__(name)
