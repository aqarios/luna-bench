from luna_quantum import Solution

from luna_bench._internal.domain_models import AlgorithmResultDomain, JobStatus


class TestAlgorithmResultDomain:
    def test_solution_setter(self, solution: Solution) -> None:
        a = AlgorithmResultDomain.model_construct(
            meta_data=None,
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
