from datetime import UTC, datetime

import cloudpickle
import pytest
from luna_model import Solution

from luna_bench.errors.decorators.invalid_return_type_error import InvalidReturnTypeError
from luna_bench.errors.metadata_decoding_error import MetadataDecodingError
from luna_bench.errors.metadata_encoding_error import MetadataEncodingError
from luna_bench.helpers.metadata import decode_metadata, encode_metadata, split_solve_outcome

_solution = Solution([])


class TestSplitSolveOutcome:
    def test_a_bare_solution_reports_no_metadata(self) -> None:
        assert split_solve_outcome(_solution, "algo") == (_solution, None)

    def test_a_pair_is_split_into_solution_and_metadata(self) -> None:
        solution, metadata = split_solve_outcome((_solution, {"device": "qpu-7"}), "algo")

        assert solution is _solution
        assert metadata == {"device": "qpu-7"}

    def test_a_mapping_is_copied_into_a_plain_dict(self) -> None:
        """The algorithm keeps its own object; what is stored is a copy of what it reported."""
        reported = {"shots": 1024}
        _, metadata = split_solve_outcome((_solution, reported), "algo")

        assert metadata == reported
        assert metadata is not reported

    @pytest.mark.parametrize(
        "outcome",
        [
            "not a solution",
            None,
            (_solution,),
            (_solution, {"a": 1}, "too much"),
            ("not a solution", {"a": 1}),
            # A list of values is the near miss worth naming: iterable, but not a mapping.
            (_solution, ["device", "qpu-7"]),
        ],
    )
    def test_anything_but_a_solution_or_a_pair_of_one_and_a_mapping_is_rejected(self, outcome: object) -> None:
        with pytest.raises(InvalidReturnTypeError):
            split_solve_outcome(outcome, "algo")  # type: ignore[arg-type] # the point of the test


class TestEncodeDecodeMetadata:
    def test_nothing_reported_stays_nothing(self) -> None:
        assert encode_metadata(None) is None
        assert decode_metadata(None) is None

    def test_a_mapping_survives_the_round_trip(self) -> None:
        metadata = {"device": "qpu-7", "shots": 1024, "nested": {"a": [1, 2, 3]}}

        assert decode_metadata(encode_metadata(metadata)) == metadata

    def test_values_json_could_not_hold_survive_too(self) -> None:
        """Serializing as bytes is what keeps a provider's own types intact."""
        metadata = {"queued_at": datetime(2026, 9, 28, 12, 0, tzinfo=UTC), "shots": {1024, 4096}}

        assert decode_metadata(encode_metadata(metadata)) == metadata

    def test_what_cannot_be_serialized_is_reported_with_the_algorithm_name(self) -> None:
        with pytest.raises(MetadataEncodingError, match="my_algorithm"):
            encode_metadata({"connection": (i for i in range(3))}, "my_algorithm")

    def test_what_cannot_be_serialized_is_reported_without_a_name_too(self) -> None:
        with pytest.raises(MetadataEncodingError, match="The metadata of a run"):
            encode_metadata({"connection": (i for i in range(3))})

    def test_bytes_that_are_not_metadata_are_reported(self) -> None:
        with pytest.raises(MetadataDecodingError):
            decode_metadata(b"not pickled at all")

    def test_bytes_holding_something_other_than_a_mapping_are_reported(self) -> None:
        with pytest.raises(MetadataDecodingError, match="dict"):
            decode_metadata(bytes(cloudpickle.dumps(["not", "a", "mapping"])))
