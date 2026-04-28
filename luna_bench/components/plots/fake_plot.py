import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.metrics.fake_metric import FakeMetric
from luna_bench.components.plots.utils.style import AqariosColours
from luna_bench.helpers.decorators import plot


@plot(required_metrics=FakeMetric)
def FakePlot(benchmark_results: BenchmarkResults) -> None:  # noqa: N802# Using a function instead of a class to show to users how to create a plot with functions.
    """Plot aggregated ``FakeMetric`` random values for each algorithm-model pair.

    Parameters
    ----------
    benchmark_results : BenchmarkResults
        Benchmark outputs containing metric results used to build the plot.
    """
    rows = []
    for model_name, algorithm_name, metrics_result in benchmark_results.get_all_metrics():
        for metric_name, metric_result in metrics_result.get_all(FakeMetric).items():
            a = {
                "algorithm": f"{algorithm_name} {model_name} {metric_name}",
                "model": model_name,
                "random_number": metric_result.random_number,
                "metric_name": metric_name,
            }
            rows.append(a)

    df = pd.DataFrame(rows)

    unique_algorithms = df["algorithm"].nunique()
    palette = AqariosColours.palette(num_colors=min(unique_algorithms, 6))

    plt.figure(figsize=(8, 5))
    sns.barplot(
        data=df,
        x="algorithm",
        y="random_number",
        errorbar="sd",
        hue="algorithm",
        palette=palette,
        legend=False,
    )
    plt.ylabel("Average random_number")
    plt.xlabel("Algorithm")
    plt.title("Average FakeMetric Value per Solver")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()
