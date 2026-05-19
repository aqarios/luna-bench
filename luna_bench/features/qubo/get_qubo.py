import numpy as np
from luna_model import Model, Sense
from luna_model.errors import ModelNotQuadraticError, ModelNotUnconstrainedError, ModelVtypeError
from luna_model.translator import QuboTranslator
from numpy.typing import NDArray


def get_qubo(model: Model) -> NDArray[np.float64]:
    """Extract the QUBO matrix from a model.

    Clone the model, negate the objective for maximization problems, and translate
    it into a QUBO matrix via ``QuboTranslator``.

    Parameters
    ----------
    model : Model
        The optimization model to extract the QUBO matrix from.

    Returns
    -------
    NDArray[np.float64]
        The QUBO matrix representation of the model.

    Raises
    ------
    RuntimeError
        If the model is not unconstrained, not quadratic, contains invalid
        variable types, or any other translation error occurs.
    """
    reduced_model = model.deep_clone()
    # ensure model is a minimization problem
    if model.sense == Sense.MAX:
        reduced_model.objective = -reduced_model.objective

    try:
        qubo_matrix = QuboTranslator.from_lm(reduced_model).matrix
    except Exception as e:
        if isinstance(e, ModelNotUnconstrainedError):
            msg = "Provided model is not unconstrained."
        elif isinstance(e, ModelNotQuadraticError):
            msg = "Provided model is not quadratic."
        elif isinstance(e, ModelVtypeError):
            msg = "Provided model contains different vtypes or vtypes other than binary and spin."
        else:
            msg = "Unknown error."
        raise RuntimeError(msg) from e
    return qubo_matrix
