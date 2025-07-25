from __future__ import annotations

from logging import Logger

from luna_quantum import Logging
from peewee import Database, _transaction

from luna_bench._internal.entities.protocols import ModelSetStorage, ModelStorage


class PeeweeTransaction(_transaction):
    _logger: Logger

    _modelset_storage: ModelSetStorage
    _model_storage: ModelStorage

    def __init__(
        self,
        database: Database,
        modelset_storage: ModelSetStorage,
        model_storage: ModelStorage,
    ) -> None:
        super().__init__(database)
        self._logger = Logging.get_logger(__name__)

        self._modelset_storage = modelset_storage
        self._model_storage = model_storage

    @property
    def modelset(self) -> ModelSetStorage:
        return self._modelset_storage

    @property
    def model(self) -> ModelStorage:
        return self._model_storage
