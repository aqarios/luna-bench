"""Tests for the get_qubo function."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from luna_quantum import Bounds, Model, Sense, Variable, Vtype
from luna_quantum.translator import QuboTranslator

from luna_bench.components.features.qubo.get_qubo import get_qubo


def create_mock_qubo_model(sense: Sense, objective: float) -> MagicMock:
    mock_model = MagicMock()
    mock_model.sense = sense
    mock_model.objective = objective
    return mock_model


def creat_mock_translator(matrix_list: list[list[float]]) -> MagicMock:
    matrix = np.array(matrix_list)
    mock_translator = MagicMock()
    mock_translator.matrix = matrix
    return mock_translator


class TestGetQubo:
    """Tests for the get_qubo helper function."""

    @pytest.mark.parametrize(
        ("input_list", "exp_list"),
        [
            ([[1.0, 4.0], [0.0, 3.0]], [[1.0, 2.0], [2.0, 3.0]]),  # upper triangular to symmetric
            ([[1.0, 0.0], [4.0, 3.0]], [[1.0, 2.0], [2.0, 3.0]]),  # lower triangular to symmetric
            ([[1.0, 2.0], [2.0, 3.0]], [[1.0, 2.0], [2.0, 3.0]]),  # symmetric stays symmetric
        ],
    )
    def test_returns_qubo_matrix_from_valid_model(
        self, input_list: list[list[float]], exp_list: list[list[float]]
    ) -> None:
        input_matrix = np.array(input_list)
        expected_matrix = np.array(exp_list)
        luna_model = QuboTranslator.to_aq(input_matrix)
        result = get_qubo(luna_model)
        np.testing.assert_array_equal(result, expected_matrix)

    @pytest.mark.parametrize(("sense", "org_obj", "exp_obj"), [(Sense.Max, -5.0, 5.0), (Sense.Min, 5.0, 5.0)])
    def test_negates_objective_for_maximization(self, sense: Sense, org_obj: float, exp_obj: float) -> None:
        mock_model = create_mock_qubo_model(sense=sense, objective=org_obj)

        cloned_model = mock_model.deep_clone.return_value
        cloned_model.objective = org_obj

        mock_translator = creat_mock_translator([[1.0]])

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.return_value = mock_translator
            get_qubo(mock_model)

        assert cloned_model.objective == exp_obj

    def test_raises_runtime_error_for_unconstrained_model(self) -> None:
        model = Model("constrained")
        with model.environment:
            x = Variable("x", vtype=Vtype.Binary)
        model.objective = 1 * x
        model.constraints += x <= 1

        with pytest.raises(RuntimeError, match="not unconstrained"):
            get_qubo(model)

    def test_raises_runtime_error_for_non_quadratic_model(self) -> None:
        model = Model("cubic")
        with model.environment:
            x = Variable("x", vtype=Vtype.Binary)
            y = Variable("y", vtype=Vtype.Binary)
            z = Variable("z", vtype=Vtype.Binary)
        model.objective = x * y * z

        with pytest.raises(RuntimeError, match="not quadratic"):
            get_qubo(model)

    def test_raises_runtime_error_for_invalid_vtype(self) -> None:
        model = Model("integer_vars")
        with model.environment:
            x = Variable("x", vtype=Vtype.Integer, bounds=Bounds(0, 5))
            y = Variable("y", vtype=Vtype.Integer, bounds=Bounds(0, 5))
        model.objective = x + y

        with pytest.raises(RuntimeError, match="different vtypes"):
            get_qubo(model)

    def test_raises_runtime_error_for_unknown_exception(self) -> None:
        mock_model = create_mock_qubo_model(Sense.Min, 0.0)

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.side_effect = ValueError("something unexpected")

            with pytest.raises(RuntimeError, match="Unknown error"):
                get_qubo(mock_model)

    def test_preserves_original_exception_as_cause(self) -> None:
        mock_model = create_mock_qubo_model(Sense.Min, 0.0)
        original_error = ValueError("original")

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.side_effect = original_error

            with pytest.raises(RuntimeError) as exc_info:
                get_qubo(mock_model)

            assert exc_info.value.__cause__ is original_error

    def test_passes_cloned_model_to_translator(self) -> None:
        mock_model = create_mock_qubo_model(Sense.Min, 0.0)
        cloned_model = mock_model.deep_clone.return_value

        mock_translator = creat_mock_translator([[1.0]])

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.return_value = mock_translator
            get_qubo(mock_model)

        mock_translator_cls.from_aq.assert_called_once_with(cloned_model)
