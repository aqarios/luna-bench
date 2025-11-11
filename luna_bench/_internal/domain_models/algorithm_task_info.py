from luna_bench._internal.domain_models.base_domain import BaseDomain


class AlgorithmTaskInfo(BaseDomain):
    model_id: int
    algorithm_name: str
    task_id: str
