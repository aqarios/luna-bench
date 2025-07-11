class Benchmark:
    """Main benchmark class."""

    def run(self) -> None:
        """Run the benchmark."""
        raise NotImplementedError

    def report(self) -> None:
        """Report the benchmark results as PDF etc."""
        raise NotImplementedError

    def analyze(self) -> None:
        """Analyze the benchmark results."""
        raise NotImplementedError

    def visualize(self) -> None:
        """Visualize the benchmark results."""
        raise NotImplementedError
