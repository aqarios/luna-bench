from luna_bench.errors.base_error import BaseError


class ModelLookupMissError(BaseError):
    """
    Raised when a model has no entry in a lookup feature's mapping.

    Attributes
    ----------
    model_name : str
        Name of the model that was not found.
    model_key : int
        The ``hash(model)`` that was looked up.
    feature_name : str
        Name of the lookup feature class that raised.
    """

    model_name: str
    model_key: int
    feature_name: str

    def __init__(self, model_name: str, model_key: int, feature_name: str) -> None:
        self.model_name = model_name
        self.model_key = model_key
        self.feature_name = feature_name
        super().__init__(
            f"{feature_name} has no entry for model '{model_name}' (key {model_key}). "
            f"Register it with .add_model(model, value) before passing the feature to Benchmark.add_feature()."
        )
