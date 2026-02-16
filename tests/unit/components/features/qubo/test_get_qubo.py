"""Tests for the get_qubo function."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from luna_quantum import Sense
from luna_quantum.errors import ModelNotQuadraticError, ModelNotUnconstrainedError, ModelVtypeError

from luna_bench.components.features.qubo.get_qubo import get_qubo


class TestGetQubo:
    """Tests for the get_qubo helper function."""

    def test_returns_qubo_matrix_from_valid_model(self) -> None:
        expected_matrix = np.array([[1.0, 2.0], [2.0, 3.0]])

        mock_model = MagicMock()
        mock_model.sense = Sense.Min

        mock_translator = MagicMock()
        mock_translator.matrix = expected_matrix

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.return_value = mock_translator
            result = get_qubo(mock_model)

        np.testing.assert_array_equal(result, expected_matrix)

    def test_clones_model_before_processing(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Min

        mock_translator = MagicMock()
        mock_translator.matrix = np.array([[1.0]])

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.return_value = mock_translator
            get_qubo(mock_model)

        mock_model.deep_clone.assert_called_once()

    def test_negates_objective_for_maximization(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Max
        mock_model.objective = 5.0

        cloned_model = mock_model.deep_clone.return_value
        cloned_model.objective = 5.0

        mock_translator = MagicMock()
        mock_translator.matrix = np.array([[1.0]])

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.return_value = mock_translator
            get_qubo(mock_model)

        assert cloned_model.objective == -5.0

    def test_does_not_negate_objective_for_minimization(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Min
        mock_model.objective = 5.0

        cloned_model = mock_model.deep_clone.return_value
        cloned_model.objective = 5.0

        mock_translator = MagicMock()
        mock_translator.matrix = np.array([[1.0]])

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.return_value = mock_translator
            get_qubo(mock_model)

        assert cloned_model.objective == 5.0

    def test_raises_runtime_error_for_unconstrained_model(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Min

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.side_effect = ModelNotUnconstrainedError()

            with pytest.raises(RuntimeError, match="not unconstrained"):
                get_qubo(mock_model)

    def test_raises_runtime_error_for_non_quadratic_model(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Min

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.side_effect = ModelNotQuadraticError()

            with pytest.raises(RuntimeError, match="not quadratic"):
                get_qubo(mock_model)

    def test_raises_runtime_error_for_invalid_vtype(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Min

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.side_effect = ModelVtypeError()

            with pytest.raises(RuntimeError, match="different vtypes"):
                get_qubo(mock_model)

    def test_raises_runtime_error_for_unknown_exception(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Min

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.side_effect = ValueError("something unexpected")

            with pytest.raises(RuntimeError, match="Unknown error"):
                get_qubo(mock_model)

    def test_preserves_original_exception_as_cause(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Min
        original_error = ValueError("original")

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.side_effect = original_error

            with pytest.raises(RuntimeError) as exc_info:
                get_qubo(mock_model)

            assert exc_info.value.__cause__ is original_error

    def test_passes_cloned_model_to_translator(self) -> None:
        mock_model = MagicMock()
        mock_model.sense = Sense.Min
        cloned_model = mock_model.deep_clone.return_value

        mock_translator = MagicMock()
        mock_translator.matrix = np.array([[1.0]])

        with patch("luna_bench.components.features.qubo.get_qubo.QuboTranslator") as mock_translator_cls:
            mock_translator_cls.from_aq.return_value = mock_translator
            get_qubo(mock_model)

        mock_translator_cls.from_aq.assert_called_once_with(cloned_model)
