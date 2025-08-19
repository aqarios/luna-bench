from .base_domain import BaseDomain
from .benchmark_status_enum import BenchmarkStatus
from .metric_config_domain import MetricConfigDomain
from .modelmetric_config_domain import ModelmetricConfigDomain
from .modelset_domain import ModelSetDomain
from .plot_config_domain import PlotConfigDomain
from .solve_job_config_domain import SolveJobConfigDomain


class BenchmarkDomain(BaseDomain):
    id: int
    name: str

    status: BenchmarkStatus

    modelset: ModelSetDomain | None

    modelmetrics: list[ModelmetricConfigDomain]

    solve_jobs: list[SolveJobConfigDomain]

    metrics: list[MetricConfigDomain]

    plots: list[PlotConfigDomain]
