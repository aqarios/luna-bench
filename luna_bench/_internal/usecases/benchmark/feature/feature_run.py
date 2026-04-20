import time
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_model import Model
from luna_quantum import Logging
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.domain_models.feature_result_domain import FeatureResultDomain
from luna_bench._internal.domain_models.model_metadata_domain import ModelMetadataDomain
from luna_bench._internal.mappers import FeatureMapper
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench._internal.usecases.benchmark.protocols import FeatureRunUc
from luna_bench.base_components import BaseFeature
from luna_bench.entities import BenchmarkEntity, FeatureEntity, FeatureResultEntity
from luna_bench.entities.enums import JobStatus
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.errors.run_errors.run_modelset_missing_error import RunModelsetMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain


class FeatureRunUcImpl(FeatureRunUc):
    _transaction: DaoTransaction
    _registry: PydanticRegistry[BaseFeature, RegisteredDataDomain]
    _logger = Logging.get_logger(__name__)

    @inject
    def __init__(
        self,
        transaction: DaoTransaction = Provide[DaoContainer.transaction],
        registry: PydanticRegistry[BaseFeature, RegisteredDataDomain] = Provide[RegistryContainer.feature_registry],
    ) -> None:
        """
        Initialize the BenchmarkAddFeatureUc with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction
        self._registry = registry

    def _run(
        self, benchmark_name: str, model_metadata: ModelMetadataDomain, model: Model, feature: FeatureEntity
    ) -> Result[FeatureResultEntity, DataNotExistError | UnknownLunaBenchError]:
        # CHECK if result for feature and model already exists and if it should be updated/recalulated or not.
        result: FeatureResultEntity | None = feature.results.get(model_metadata.name, None)

        if result is not None and result.status == JobStatus.DONE:
            self._logger.info(f"Feature {feature.name} for model {model_metadata.name} already exists and is done.")
            return Success(result)

        user_result: ArbitraryDataDomain | None = None
        exception: str | None = None
        status: JobStatus

        start = time.perf_counter_ns()

        try:
            user_result = feature.feature.run(model)
            status = JobStatus.DONE
        except Exception as e:
            self._logger.error(f"Feature '{feature.name}' failed on model '{model_metadata.name}':", exc_info=True)
            status = JobStatus.FAILED
            exception = str(e)

        end = time.perf_counter_ns()

        delta_time = (end - start) // 1_000_000

        # Save result. Doesn't matter if it failed or not, we have to save it anyway.
        result_domain = FeatureResultDomain.model_construct(
            processing_time_ms=delta_time,
            model_name=model_metadata.name,
            result=user_result,
            status=status,
            error=exception,
        )
        with self._transaction as t:
            r: Result[None, DataNotExistError | UnknownLunaBenchError] = t.feature.set_result(
                benchmark_name,
                feature.name,
                result_domain,
            )
        if not is_successful(r):
            return Failure(r.failure())

        result = FeatureMapper.result_to_user_model(result_domain)
        feature.results[model_metadata.name] = result
        return Success(result)

    def __call__(
        self, benchmark: BenchmarkEntity, feature: FeatureEntity | None = None
    ) -> Result[None, RunFeatureMissingError | RunModelsetMissingError]:
        features: list[FeatureEntity]
        if feature is not None:
            # Check if the feature is part of the benchmark
            if feature not in benchmark.features:
                return Failure(RunFeatureMissingError(feature.name, benchmark.name))
            features = [feature]
        else:
            features = benchmark.features

        if benchmark.modelset is None:
            return Failure(RunModelsetMissingError(benchmark.name))

        for model in benchmark.modelset.models:
            with self._transaction as t:
                # TODO(Llewellyn): the model loading her can be optimized a lot.  # noqa: FIX002
                #  Best to probably do just one query and for that a new dao method is needed.
                #  Also maybe change the ANY in ModelMetadataDomain to Model or bytes
                model_metadata = t.model.get(model.hash).unwrap()
                model_bytes = t.model.load(model_metadata.id).unwrap()
                m = Model.decode(model_bytes)

            for f in features:
                result: Result[FeatureResultEntity, DataNotExistError | UnknownLunaBenchError] = self._run(
                    benchmark.name, model_metadata, m, f
                )
                if not is_successful(result):
                    pass  # TODO(Llewellyn): decide what to do with the failed run # noqa: FIX002
        return Success(None)
