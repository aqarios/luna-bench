from __future__ import annotations

from typing import TYPE_CHECKING

from luna_quantum import Logging

from . import ModelSetStorage

if TYPE_CHECKING:
    from logging import Logger


class BenchmarkDao(ModelSetStorage):
    _logger: Logger = Logging.get_logger(__name__)
