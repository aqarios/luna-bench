from __future__ import annotations

from logging import Logger

from luna_quantum import Logging
from peewee import _transaction

from luna_bench._internal.entities.model_set.dao import ModelSetDAO
from luna_bench._internal.shared.database.base_model import database


class PeeweeTransaction(_transaction):
    _logger: Logger

    def __init__(self) -> None:
        super().__init__(database)

        self._logger = Logging.get_logger(__name__)

    @property
    def model_set(self) -> ModelSetDAO:
        return ModelSetDAO()
