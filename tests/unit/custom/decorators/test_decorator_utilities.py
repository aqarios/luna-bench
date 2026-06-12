from typing import Any, cast

import pytest
from luna_model import Model

from luna_bench.custom.decorators.decorator_utilities import DecoratorUtilities
from luna_bench.errors.decorators.invalid_parameter_type_error import InvalidParameterTypeError
from luna_bench.errors.decorators.invalid_signature_error import InvalidSignatureError


def test_validate_signature_wrong_params() -> None:
    def bad_func(x: Model) -> object:
        return x

    with pytest.raises(InvalidSignatureError):
        DecoratorUtilities.validate_signature(bad_func, parameter_map={"model": Model})


def test_validate_signature_wrong_type() -> None:
    def bad_func(model: int) -> object:
        return model

    with pytest.raises(InvalidParameterTypeError):
        DecoratorUtilities.validate_signature(bad_func, parameter_map={"model": Model})


def test_split_components_invalid_type() -> None:
    with pytest.raises(TypeError, match="must contain only BaseFeature or BaseMetric"):
        DecoratorUtilities.split_components(cast("Any", "invalid"))
