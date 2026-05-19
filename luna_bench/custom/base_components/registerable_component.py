from typing import ClassVar

from pydantic import BaseModel


class RegisterableComponent(BaseModel):
    """Base class for components that can be registered in a registry."""

    registered_id: ClassVar[str]
