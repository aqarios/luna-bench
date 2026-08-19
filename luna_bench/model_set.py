from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Final

from dependency_injector.wiring import Provide, inject
from luna_model import Model
from returns.pipeline import is_successful

from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench.entities import ModelSetEntity
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.logging import BenchLogger
from luna_bench.model_metadata import ModelMetadata

if TYPE_CHECKING:
    from logging import Logger

    from returns.result import Result

    from luna_bench._internal.usecases import ModelLoadAllUc
    from luna_bench._internal.usecases.modelset.protocols import (
        ModelAddUc,
        ModelRemoveUc,
        ModelSetCreateUc,
        ModelSetDeleteUc,
        ModelSetLoadAllUc,
        ModelSetLoadUc,
    )
    from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
    from luna_bench.errors.model_name_already_used_error import ModelNameAlreadyUsedError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


MODEL_FILE_SUFFIXES: Final = (".lp", ".mps")

type ModelSource = Model | str | Path | Iterable[ModelSource]
"""Anything that can be turned into models: a ``Model``, a path to an ``.lp`` or
``.mps`` file, a path to a directory of such files, or an iterable of those,
nested to any depth."""


def _load_model_file(path: Path) -> Model:
    """Load a single model file, naming the model after the file stem.

    The stem wins over the name recorded *inside* the file because it is a
    function of the path alone, so ``remove_model(path)`` resolves to the same
    name ``add(path)`` stored it under. It also keeps a batch unique: a file
    carrying no name at all loads as ``"unnamed"``, and model names are unique
    across the database, so the second such file in a folder would clash.

    The path itself is deliberately not folded into the name - a name is not a
    place to keep provenance, and it is capped at 45 characters. That waits for
    ``Model`` to support metadata.
    """
    model = Model.from_(path)
    model.name = path.stem
    return model


def _load_models_from_path(path: Path) -> list[Model]:
    """Load every model file at ``path``, which may be a file or a directory."""
    suffixes = " or ".join(MODEL_FILE_SUFFIXES)

    if not path.exists():
        msg = (
            f"No such file or directory: '{path}'. Pass a Model, an iterable of Models, or a path "
            f"to a {suffixes} file or to a directory containing such files."
        )
        raise FileNotFoundError(msg)

    if not path.is_dir():
        return [_load_model_file(path)]

    files = sorted(p for p in path.iterdir() if p.suffix in MODEL_FILE_SUFFIXES)
    if not files:
        msg = f"Directory '{path}' contains no {suffixes} files."
        raise FileNotFoundError(msg)

    return [_load_model_file(p) for p in files]


def _as_models(candidate: ModelSource) -> list[Model]:
    """Flatten whatever ``add`` / ``remove_model`` was given into a list of models.

    Paths - single files or directories - are read from disk; iterables are
    flattened recursively. ``str`` and ``Path`` are handled before ``Iterable``
    so a string is read as a path rather than iterated character by character.
    """
    if isinstance(candidate, str | Path):
        return _load_models_from_path(Path(candidate))

    if isinstance(candidate, Iterable):
        return [model for item in candidate for model in _as_models(item)]

    return [candidate]


class ModelSet(ModelSetEntity):
    """
    Set of models.

    Represents a collection of models with operations for creating, loading, adding,
    removing, and deleting models.

    Attributes
    ----------
    id : int
        The unique identifier for the model set.
    name : str
        The name of the model set.
    models : list[ModelMetadata]
        A list of ModelData objects representing the models in this set.
    """

    _logger: ClassVar[Logger] = BenchLogger.get_logger(__name__)

    @staticmethod
    @inject
    def __create_uc(
        modelset_create: ModelSetCreateUc = Provide[UsecaseContainer.modelset_create_uc],
    ) -> ModelSetCreateUc:
        return modelset_create

    @staticmethod
    @inject
    def __load_uc(
        modelset_load: ModelSetLoadUc = Provide[UsecaseContainer.modelset_load_uc],
    ) -> ModelSetLoadUc:
        return modelset_load

    @staticmethod
    @inject
    def __load_all_uc(
        modelset_load_all: ModelSetLoadAllUc = Provide[UsecaseContainer.modelset_load_all_uc],
    ) -> ModelSetLoadAllUc:
        return modelset_load_all

    @staticmethod
    @inject
    def __model_all_uc(
        model_all: ModelLoadAllUc = Provide[UsecaseContainer.model_load_all_uc],
    ) -> ModelLoadAllUc:
        return model_all

    @staticmethod
    @inject
    def __model_add_uc(
        modelset_add: ModelAddUc = Provide[UsecaseContainer.model_add_uc],
    ) -> ModelAddUc:
        return modelset_add

    @staticmethod
    @inject
    def __model_remove_uc(
        modelset_remove: ModelRemoveUc = Provide[UsecaseContainer.model_remove_uc],
    ) -> ModelRemoveUc:
        return modelset_remove

    @staticmethod
    @inject
    def __delete_uc(
        modelset_delete_uc: ModelSetDeleteUc = Provide[UsecaseContainer.modelset_delete_uc],
    ) -> ModelSetDeleteUc:
        return modelset_delete_uc

    @staticmethod
    def create(
        modelset_name: str,
    ) -> ModelSet:
        """
        Create a new model set with the given dataset name.

        Creates a new model set using the provided dataset name and a model
        set creation use case.

        Parameters
        ----------
        modelset_name : str
            The name of the dataset.

        Returns
        -------
        ModelSet
            An instance of ModelSet representing the successfully created model set.
        """
        modelset_create = ModelSet.__create_uc()

        result: Result[ModelSetEntity, DataNotUniqueError | UnknownLunaBenchError] = modelset_create(
            modelset_name=modelset_name
        )

        if not is_successful(result):
            error = result.failure()
            match error:
                case DataNotUniqueError():
                    ModelSet._logger.warning(
                        f"Modelset '{modelset_name}' does already exist. "
                        f'Loading it with `ModelSet.load("{modelset_name}")`.'
                    )
                    return ModelSet.load(modelset_name)
                case _:
                    ModelSet._logger.info(f"Error: {error}")
                    raise RuntimeError(error)

        return ModelSet.model_validate(result.unwrap(), from_attributes=True)

    @staticmethod
    def load(name: str) -> ModelSet:
        """
        Load a model set by its ID.

        Retrieves a model set from the database using its unique identifier.

        Parameters
        ----------
        name : str
            The unique name of the model set to load.


        Returns
        -------
        ModelSet
            The loaded model set.
        """
        modelset_load = ModelSet.__load_uc()

        result: Result[ModelSetEntity, DataNotExistError | UnknownLunaBenchError] = modelset_load(modelset_name=name)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

        return ModelSet.model_validate(result.unwrap(), from_attributes=True)

    @staticmethod
    def load_all() -> list[ModelSet]:
        """
        Load all model sets from the database.

        Retrieves all model sets stored in the database.

        Returns
        -------
        list[ModelSet]
            A list of all model sets.
        """
        modelset_load_all = ModelSet.__load_all_uc()

        result: Result[list[ModelSetEntity], UnknownLunaBenchError] = modelset_load_all()

        if not is_successful(result):
            error = result.failure()
            raise RuntimeError(error)
        # TODO(Llewellyn): i think model validate for metadata is here missing # noqa: FIX002
        return [ModelSet.model_validate(m, from_attributes=True) for m in result.unwrap()]

    @staticmethod
    def load_all_models() -> list[ModelMetadata]:
        """
        Load all models from the database.

        Retrieves all models stored in the database, regardless of which model set they belong to.

        Returns
        -------
        list[ModelMetadata]
            A list of ModelData objects representing all models in the database.
        """
        model_all = ModelSet.__model_all_uc()
        return [ModelMetadata.model_validate(m, from_attributes=True) for m in model_all()]

    def add(
        self,
        model: ModelSource,
    ) -> None:
        """
        Add a model to this model set.

        Adds the specified model to this model set and updates the model set's state.

        Models already present in this model set are skipped with a warning
        instead of being duplicated, so re-running the same script is safe.

        Models are added one at a time and each one is committed on its own, so
        a failure part-way through an iterable leaves the earlier models added.

        Parameters
        ----------
        model : ModelSource
            The model to add to this model set. It can be

            - a ``Model``,
            - a path (``str`` or ``Path``) to an ``.lp`` or ``.mps`` file,
            - a path to a directory, in which case every ``.lp`` and ``.mps``
              file directly inside it is added, in file-name order,
            - an iterable mixing any of the above, nested to any depth, in
              which case all of them are added.

            Models loaded from a file are named after the file stem, not after
            the name recorded inside the file.

        Raises
        ------
        FileNotFoundError
            Raised if a given path does not exist, or is a directory holding no
            ``.lp`` or ``.mps`` files.
        ValueError
            Raised if a given file is neither an ``.lp`` nor an ``.mps`` file.
        ModelNameAlreadyUsedError
            Raised if a *different* model already uses the same name.
        """
        for single in _as_models(model):
            self._add_one(single)

    def _add_one(self, model: Model) -> None:
        """Add exactly one model, skipping it with a warning if it is already here."""
        if self._holds(model):
            ModelSet._logger.warning(f"Model '{model.name}' is already in modelset '{self.name}'. Skipping it.")
            return

        modelset_add = self.__model_add_uc()

        result: Result[ModelSetEntity, DataNotExistError | ModelNameAlreadyUsedError | UnknownLunaBenchError] = (
            modelset_add(modelset_name=self.name, model=model)
        )

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error adding model '{model.name}': {error}")
            raise error
        self._update(result.unwrap())

    def remove_model(
        self,
        model: ModelSource,
    ) -> None:
        """
        Remove a model from this model set.

        Removes the specified model from this model set and updates the model set's state.

        Parameters
        ----------
        model : ModelSource
            The model to remove from this model set. It accepts everything
            ``add`` accepts: a ``Model``, a path to an ``.lp``/``.mps`` file, a
            path to a directory of such files, or an iterable of those.

            Models are removed one at a time and each removal is committed on
            its own. If one of them fails, the earlier ones stay removed and the
            raised ``RuntimeError`` names them.

        Raises
        ------
        FileNotFoundError
            Raised if a given path does not exist, or is a directory holding no
            ``.lp`` or ``.mps`` files.
        ValueError
            Raised if a given file is neither an ``.lp`` nor an ``.mps`` file.
        """
        removed: list[str] = []

        for single in _as_models(model):
            try:
                self._remove_one(single)
            except RuntimeError as error:
                if removed:
                    msg = (
                        f"Removal stopped at model '{single.name}': {error} Models {removed} were already "
                        f"removed from modelset '{self.name}' and are gone; the rest were not touched."
                    )
                    raise RuntimeError(msg) from error
                raise
            removed.append(single.name)

    def _remove_one(self, model: Model) -> None:
        """Remove exactly one model from this model set."""
        modelset_remove = self.__model_remove_uc()

        result: Result[ModelSetEntity, DataNotExistError | UnknownLunaBenchError] = modelset_remove(
            modelset_name=self.name, model=model
        )

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)
        self._update(result.unwrap())

    def delete(self) -> None:
        """
        Delete this model set from the database.

        Permanently removes this model set from the database.
        """
        modelset_delete_uc = self.__delete_uc()

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = modelset_delete_uc(modelset_name=self.name)

        if not is_successful(result):
            error = result.failure()
            ModelSet._logger.info(f"Error: {error}")
            raise RuntimeError(error)

    def _holds(self, model: Model) -> bool:
        """Return whether this model set already holds exactly this model.

        Identity is the model's name plus its contents, so a changed model
        reusing a known name is not mistaken for one already present.

        ``Model.__hash__`` deliberately plays no part here: parsing one ``.mps``
        file twice yields its constraints in a different order, which changes the
        model's serialization and therefore its hash. ``equal_contents`` ignores
        constraint order, so it is the identity that survives a reload.
        """
        for metadata in self.models:
            if metadata.name != model.name:
                continue
            try:
                stored = ModelMetadata.model_validate(metadata, from_attributes=True).model
            except RuntimeError as error:
                # Contents unavailable: leave the decision to the use case.
                ModelSet._logger.debug(f"Could not read stored model '{metadata.name}': {error}")
                return False
            return stored.equal_contents(model)

        return False

    def _update(self, modelset: ModelSetEntity) -> None:
        """
        Update this model set with data from a domain model.

        Updates the properties of this model set with values from the provided domain model.

        Parameters
        ----------
        modelset : ModelSetDomain
            The domain model containing the updated data.
        """
        self.id = modelset.id
        self.name = modelset.name
        self.models = [ModelMetadata.model_validate(m, from_attributes=True) for m in modelset.models]
