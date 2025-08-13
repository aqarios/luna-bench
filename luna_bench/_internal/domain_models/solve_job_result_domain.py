from luna_quantum import Solution
from pydantic import BaseModel

from .base_domain import BaseDomain


class SolveJobResultDomain(BaseDomain):
    id: int

    meta_data: BaseModel
    solution: Solution
