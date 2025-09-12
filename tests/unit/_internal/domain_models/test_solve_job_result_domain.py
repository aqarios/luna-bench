from luna_quantum import Solution

from luna_bench._internal.domain_models import AlgorithmResultDomain


class TestSolveJobResultDomain:
    def test_result_domain_bytes(self, solution: Solution) -> None:
        s = AlgorithmResultDomain(meta_data=AlgorithmResultDomain.AlgorithmResultMetadata(something="xD"))
        s.solution = solution

        assert s.solution == solution

        s.solution = solution.encode()
        assert s.solution == solution
