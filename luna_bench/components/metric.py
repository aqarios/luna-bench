class Metric:
    name: str
    benchamrk_id: int

    results: list[MetricResults]

    def run(self) -> None: ...

    def result(self): ...

    def reset(self): ...
