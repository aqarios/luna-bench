import pytest

from luna_bench.custom import SolveMetadata
from luna_bench.errors.components.algorithms.metadata_not_available_error import MetadataNotAvailableError


class TestReportedMetadata:
    """A run that reported metadata answers about its own content."""

    @pytest.fixture()
    def metadata(self) -> SolveMetadata:
        return SolveMetadata(data={"device": "qpu-7", "shots": 1024})

    def test_it_is_available(self, metadata: SolveMetadata) -> None:
        assert metadata.available is True

    def test_a_reported_key_is_returned(self, metadata: SolveMetadata) -> None:
        assert metadata["device"] == "qpu-7"
        assert metadata.get("shots") == 1024

    def test_a_key_that_was_not_reported_raises(self, metadata: SolveMetadata) -> None:
        """Missing from metadata that exists is a KeyError, not an absent-metadata error."""
        with pytest.raises(KeyError):
            _ = metadata["queue_time_s"]

    def test_a_key_that_was_not_reported_falls_back_to_the_default(self, metadata: SolveMetadata) -> None:
        assert metadata.get("queue_time_s", 0.0) == 0.0
        assert metadata.get("queue_time_s") is None

    def test_membership_answers_for_reported_keys(self, metadata: SolveMetadata) -> None:
        assert "device" in metadata
        assert "queue_time_s" not in metadata

    def test_the_whole_mapping_is_available(self, metadata: SolveMetadata) -> None:
        assert metadata.as_dict() == {"device": "qpu-7", "shots": 1024}


class TestAbsentMetadata:
    """A run that reported nothing is not a run that reported an empty mapping."""

    @pytest.fixture()
    def metadata(self) -> SolveMetadata:
        return SolveMetadata()

    def test_it_is_not_available(self, metadata: SolveMetadata) -> None:
        assert metadata.available is False

    def test_reading_a_key_raises(self, metadata: SolveMetadata) -> None:
        with pytest.raises(MetadataNotAvailableError):
            _ = metadata["device"]

    def test_get_raises_rather_than_answering_with_the_default(self, metadata: SolveMetadata) -> None:
        with pytest.raises(MetadataNotAvailableError):
            metadata.get("device", "unknown")

    def test_reading_the_whole_mapping_raises(self, metadata: SolveMetadata) -> None:
        with pytest.raises(MetadataNotAvailableError):
            metadata.as_dict()

    def test_membership_is_false_rather_than_an_error(self, metadata: SolveMetadata) -> None:
        """Asking whether a key is there is how a metric checks before reading."""
        assert "device" not in metadata


class TestOf:
    def test_it_wraps_a_reported_mapping(self) -> None:
        assert SolveMetadata.of({"device": "qpu-7"}).as_dict() == {"device": "qpu-7"}

    def test_it_keeps_an_absent_mapping_absent(self) -> None:
        assert SolveMetadata.of(None).available is False

    def test_an_empty_mapping_counts_as_reported(self) -> None:
        """A solver that reports an empty mapping did report - there is just nothing in it."""
        empty = SolveMetadata.of({})

        assert empty.available is True
        assert empty.as_dict() == {}
