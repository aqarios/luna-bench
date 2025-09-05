from luna_quantum import Solution

from luna_bench._internal.domain_models import SolveJobResultDomain


class TestSolveJobResultDomain:
    def test_result_domain_bytes(self, solution: Solution) -> None:
        s = SolveJobResultDomain(meta_data=SolveJobResultDomain.SolveJobResultMetadata(something="xD"))
        s.solution = solution

        assert s.solution == solution

        s.solution = solution.encode()
        assert s.solution == solution
