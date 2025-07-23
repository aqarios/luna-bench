from luna_bench.errors.base_error import BaseError


class ModelAlreadyExistsError(BaseError):
    def __init__(self, model_name: str):
        super().__init__(f"The model '{model_name}' already exists.")
