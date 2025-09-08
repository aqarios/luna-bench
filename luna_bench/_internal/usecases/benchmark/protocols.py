

from typing import Protocol

from returns.result import Result

from luna_bench._internal.domain_models.benchmark_domain import BenchmarkDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class BenchmarkCreateUc(Protocol):
    def __call__(self, benchmark_name:str) -> Result[BenchmarkDomain, DataNotUniqueError| UnknownLunaBenchError]:...

class BenchmarkDeleteUc(Protocol):
    def __call__(self, benchmark_name:str) -> Result[None, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkLoadUc(Protocol):
    def __call__(self, benchmark_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkLoadAllUc(Protocol):
    def __call__(self) -> Result[list[BenchmarkDomain], UnknownLunaBenchError]:...

class BenchmarkSetModelsetUc(Protocol):
    def __call__(self, benchmark_name:str, modelset_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkRemoveModelsetUc(Protocol):
    def __call__(self, benchmark_name:str, modelset_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkAddModelMetricUc(Protocol):
    def __call__(self, benchmark_name:str, model_metric_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkRemoveModelMetricUc(Protocol):
    def __call__(self, benchmark_name:str, model_metric_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkAddMetricUc(Protocol):
    def __call__(self, benchmark_name:str, metric_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkRemoveMetricUc(Protocol):
    def __call__(self, benchmark_name:str, metric_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkAddPlotUc(Protocol):
    def __call__(self, benchmark_name:str, plot_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkRemovePlotUc(Protocol):
    def __call__(self, benchmark_name:str, plot_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkAddSolveJobUc(Protocol):
    def __call__(self, benchmark_name:str, solvejob_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...

class BenchmarkRemoveSolveJobUc(Protocol):
    def __call__(self, benchmark_name:str, solvejob_name:str) -> Result[BenchmarkDomain, DataNotExistError| UnknownLunaBenchError]:...