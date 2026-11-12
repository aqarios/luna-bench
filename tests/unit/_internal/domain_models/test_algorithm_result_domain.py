from luna_model import Solution

from luna_bench._internal.domain_models import AlgorithmResultDomain
from luna_bench.entities import JobStatus
from luna_bench.helpers.metadata import decode_metadata, encode_metadata


class TestAlgorithmResultDomain:
    def test_solution_setter(self, solution: Solution) -> None:
        a = AlgorithmResultDomain.model_construct(
            model_id=1,
            status=JobStatus.DONE,
            error=None,
            task_id=None,
            retrival_data=None,
        )
        encoded_solution = solution.encode()

        def check_set() -> None:
            assert a.solution is not None
            assert a.solution.encode() == encoded_solution
            assert a.solution_bytes == encoded_solution

        def check_unset() -> None:
            assert a.solution is None
            assert a.solution_bytes is None

        check_unset()
        a.solution = solution
        check_set()

        a.solution = None
        check_unset()

        a.solution_bytes = encoded_solution
        check_set()

        a.solution = None
        check_unset()

        a.solution = encoded_solution
        check_set()

    def test_metadata_setter(self) -> None:
        a = AlgorithmResultDomain.model_construct(
            model_id=1,
            status=JobStatus.DONE,
            error=None,
            task_id=None,
            retrival_data=None,
        )
        metadata = {"device": "qpu-7"}
        encoded = encode_metadata(metadata)

        def check_set() -> None:
            assert a.metadata == metadata
            assert a.metadata_bytes is not None
            assert decode_metadata(a.metadata_bytes) == metadata

        def check_unset() -> None:
            assert a.metadata is None
            assert a.metadata_bytes is None

        check_unset()
        a.metadata = metadata
        check_set()

        a.metadata = None
        check_unset()

        a.metadata_bytes = encoded
        check_set()

        a.metadata_bytes = None
        check_unset()

        a.metadata = encoded
        check_set()
