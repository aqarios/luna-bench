import pytest
from luna_model import Solution

from luna_bench.custom import BaseMetadataMetric, BaseMetric, MetricResult, SolveMetadata, metric
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.errors.components.algorithms.metadata_not_available_error import MetadataNotAvailableError


class DeviceResult(MetricResult):
    device: str


@metric
class DeviceMetric(BaseMetadataMetric[DeviceResult]):
    """Reports which device a run was executed on."""

    def run_with_metadata(
        self,
        solution: Solution,  # noqa: ARG002
        feature_results: FeatureResultContainer,  # noqa: ARG002
        metadata: SolveMetadata,
    ) -> DeviceResult:
        return DeviceResult(device=metadata["device"])


@pytest.fixture()
def empty_features() -> FeatureResultContainer:
    return FeatureResultContainer.model_construct(data={})


class TestMetadataMetric:
    def test_it_reads_the_metadata_it_is_given(self, empty_features: FeatureResultContainer) -> None:
        result = DeviceMetric().run_with_metadata(Solution([]), empty_features, SolveMetadata.of({"device": "qpu-7"}))

        assert result.device == "qpu-7"

    def test_calling_run_without_metadata_raises_on_the_first_read(
        self, empty_features: FeatureResultContainer
    ) -> None:
        """``run`` is the path outside a benchmark, where no run is being evaluated."""
        with pytest.raises(MetadataNotAvailableError):
            DeviceMetric().run(Solution([]), empty_features)

    def test_it_is_a_metric_like_any_other(self) -> None:
        """Subclassing is what a metadata metric opts into, not a separate component kind."""
        assert isinstance(DeviceMetric(), BaseMetric)
        assert DeviceMetric.registered_id.endswith("DeviceMetric")
