from typing import Any, ClassVar

from luna_bench.base_components import BaseFeature

from .registered_class_meta import RegisteredClassMeta


class MetricClassMeta(RegisteredClassMeta):
    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs: Any):
        # Warn if the subclass explicitly defines registered_id in the class body.
        # (You can flip this logic if you only want to warn on "non-None" etc.)
        if "required_features" in namespace:
            import warnings

            warnings.warn(
                f"{name}.required_features is already defined in the class body; "
                f"the metaclass would normally inject a default. Keeping the provided value.",
                category=RuntimeWarning,
                stacklevel=2,
            )
        else:
            ann = ClassVar[tuple[BaseFeature, ...] | None]
            annotations: dict[str, Any] = namespace.setdefault("__annotations__", {})
            annotations.setdefault("required_features", ann)

        return super().__new__(mcls, name, bases, namespace, **kwargs)

    def __setattr__(cls, name: str, value: Any) -> None:
        if name == "required_features" and "required_features" in cls.__dict__:
            raise AttributeError(f"{cls.__name__}.registered_id is write-once and cannot be changed.")
        super().__setattr__(name, value)

    def __getattribute__(cls, name: str) -> Any:
        if name == "required_features" and name not in cls.__dict__:
            RegisteredClassMeta.logger.warning(
                f"{cls.__name__}.{name} was accessed but the class is not registered.Setting the value to none."
            )
            cls.required_features = None
        return super().__getattribute__(name)
