from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature
from luna_quantum import Vtype

from .utils import constraint_matrix, mean, median, vc, q10, q90

if TYPE_CHECKING:
    from luna_quantum import Model


class VariableConstraintGraphFeaturesResult(ArbitraryDataDomain):
    """
    Result container for variable-constraint graph feature calculations.

    This class stores graph-based statistics for variables and constraints,
    including node degree measures for continuous, non-continuous, and all
    variable/constraint types.

    Attributes
    ----------
    mean_variable_node_degree_continuous : float
        Mean node degree for continuous variables.
    median_variable_node_degree_continuous : float
        Median node degree for continuous variables.
    vc_variable_node_degree_continuous : float
        Variation coefficient of node degrees for continuous variables.
    q90_variable_node_degree_continuous : float
        90th percentile of node degrees for continuous variables.
    q10_variable_node_degree_continuous : float
        10th percentile of node degrees for continuous variables.
    mean_variable_node_degree_non_continuous : float
        Mean node degree for non-continuous variables.
    median_variable_node_degree_non_continuous : float
        Median node degree for non-continuous variables.
    vc_variable_node_degree_non_continuous : float
        Variation coefficient of node degrees for non-continuous variables.
    q90_variable_node_degree_non_continuous : float
        90th percentile of node degrees for non-continuous variables.
    q10_variable_node_degree_non_continuous : float
        10th percentile of node degrees for non-continuous variables.
    mean_variable_node_degree_all : float
        Mean node degree for all variables.
    median_variable_node_degree_all : float
        Median node degree for all variables.
    vc_variable_node_degree_all : float
        Variation coefficient of node degrees for all variables.
    q90_variable_node_degree_all : float
        90th percentile of node degrees for all variables.
    q10_variable_node_degree_all : float
        10th percentile of node degrees for all variables.
    mean_constraint_node_degree : float
        Mean node degree for all constraints.
    median_constraint_node_degree : float
        Median node degree for all constraints.
    vc_constraint_node_degree : float
        Variation coefficient of constraint node degrees.
    q90_constraint_node_degree : float
        90th percentile of constraint node degrees.
    q10_constraint_node_degree : float
        10th percentile of constraint node degrees.
    mean_constraint_node_degree_continuous : float
        Mean node degree for continuous constraints.
    median_constraint_node_degree_continuous : float
        Median node degree for continuous constraints.
    vc_constraint_node_degree_continuous : float
        Variation coefficient of node degrees for continuous constraints.
    q90_constraint_node_degree_continuous : float
        90th percentile of node degrees for continuous constraints.
    q10_constraint_node_degree_continuous : float
        10th percentile of node degrees for continuous constraints.
    mean_constraint_node_degree_non_continuous : float
        Mean node degree for non-continuous constraints.
    median_constraint_node_degree_non_continuous : float
        Median node degree for non-continuous constraints.
    vc_constraint_node_degree_non_continuous : float
        Variation coefficient of node degrees for non-continuous constraints.
    q90_constraint_node_degree_non_continuous : float
        90th percentile of node degrees for non-continuous constraints.
    q10_constraint_node_degree_non_continuous : float
        10th percentile of node degrees for non-continuous constraints.
    """

    # Variable node degree statistics - continuous
    mean_variable_node_degree_continuous: float
    median_variable_node_degree_continuous: float
    vc_variable_node_degree_continuous: float
    q90_variable_node_degree_continuous: float
    q10_variable_node_degree_continuous: float

    # Variable node degree statistics - non-continuous
    mean_variable_node_degree_non_continuous: float
    median_variable_node_degree_non_continuous: float
    vc_variable_node_degree_non_continuous: float
    q90_variable_node_degree_non_continuous: float
    q10_variable_node_degree_non_continuous: float

    # Variable node degree statistics - all
    mean_variable_node_degree_all: float
    median_variable_node_degree_all: float
    vc_variable_node_degree_all: float
    q90_variable_node_degree_all: float
    q10_variable_node_degree_all: float

    # Constraint node degree statistics - all
    mean_constraint_node_degree: float
    median_constraint_node_degree: float
    vc_constraint_node_degree: float
    q90_constraint_node_degree: float
    q10_constraint_node_degree: float

    # Constraint node degree statistics - continuous
    mean_constraint_node_degree_continuous: float
    median_constraint_node_degree_continuous: float
    vc_constraint_node_degree_continuous: float
    q90_constraint_node_degree_continuous: float
    q10_constraint_node_degree_continuous: float

    # Constraint node degree statistics - non-continuous
    mean_constraint_node_degree_non_continuous: float
    median_constraint_node_degree_non_continuous: float
    vc_constraint_node_degree_non_continuous: float
    q90_constraint_node_degree_non_continuous: float
    q10_constraint_node_degree_non_continuous: float


@feature
class VariableConstraintGraphFeatures(IFeature):
    """
    Feature extractor for variable-constraint graph properties.

    Calculates node degree statistics for variables and constraints in the
    bipartite graph representation of an optimization model. Computes statistics
    separately for continuous and non-continuous variables/constraints.
    """

    def run(self, model: Model) -> ArbitraryDataDomain:
        """
        Calculate variable-constraint graph features.

        Computes node degree statistics (mean, median, variation coefficient,
        and quantiles) for variables and constraints, grouped by variable type.

        Parameters
        ----------
        model : Model
            The optimization model for which the features should be calculated.

        Returns
        -------
        VariableConstraintGraphFeaturesResult
            Container with graph-based statistical measures.
        """
        # Continuous
        Ac = constraint_matrix(model, degree=1, vtype=Vtype.Real)
        Ac_binary = (Ac != 0).astype(int)
        Ac_vnd = np.sum(Ac_binary, axis=0)  # Variable node degrees
        Ac_cnd = np.sum(Ac_binary, axis=1)  # Constraint node degrees

        # Non-continuous
        Anc = constraint_matrix(model, degree=1, vtype=[Vtype.Integer, Vtype.Binary])
        Anc_binary = (Anc != 0).astype(int)
        Anc_vnd = np.sum(Anc_binary, axis=0)
        Anc_cnd = np.sum(Anc_binary, axis=1)

        # All variables
        Av = constraint_matrix(model, degree=1, vtype=None)
        Av_binary = (Av != 0).astype(int)
        Av_vnd = np.sum(Av_binary, axis=0)
        Av_cnd = np.sum(Av_binary, axis=1)

        return VariableConstraintGraphFeaturesResult(
            # Variable node degree statistics - continuous
            mean_variable_node_degree_continuous=mean(Ac_vnd),
            median_variable_node_degree_continuous=median(Ac_vnd),
            vc_variable_node_degree_continuous=vc(Ac_vnd),
            q90_variable_node_degree_continuous=q90(Ac_vnd),
            q10_variable_node_degree_continuous=q10(Ac_vnd),
            # Variable node degree statistics - non-continuous
            mean_variable_node_degree_non_continuous=mean(Anc_vnd),
            median_variable_node_degree_non_continuous=median(Anc_vnd),
            vc_variable_node_degree_non_continuous=vc(Anc_vnd),
            q90_variable_node_degree_non_continuous=q90(Anc_vnd),
            q10_variable_node_degree_non_continuous=q10(Anc_vnd),
            # Variable node degree statistics - all
            mean_variable_node_degree_all=mean(Av_vnd),
            median_variable_node_degree_all=median(Av_vnd),
            vc_variable_node_degree_all=vc(Av_vnd),
            q90_variable_node_degree_all=q90(Av_vnd),
            q10_variable_node_degree_all=q10(Av_vnd),
            # Constraint node degree statistics - all
            mean_constraint_node_degree=mean(Av_cnd),
            median_constraint_node_degree=median(Av_cnd),
            vc_constraint_node_degree=vc(Av_cnd),
            q90_constraint_node_degree=q90(Av_cnd),
            q10_constraint_node_degree=q10(Av_cnd),
            # Constraint node degree statistics - continuous
            mean_constraint_node_degree_continuous=mean(Ac_cnd),
            median_constraint_node_degree_continuous=median(Ac_cnd),
            vc_constraint_node_degree_continuous=vc(Ac_cnd),
            q90_constraint_node_degree_continuous=q90(Ac_cnd),
            q10_constraint_node_degree_continuous=q10(Ac_cnd),
            # Constraint node degree statistics - non-continuous
            mean_constraint_node_degree_non_continuous=mean(Anc_cnd),
            median_constraint_node_degree_non_continuous=median(Anc_cnd),
            vc_constraint_node_degree_non_continuous=vc(Anc_cnd),
            q90_constraint_node_degree_non_continuous=q90(Anc_cnd),
            q10_constraint_node_degree_non_continuous=q10(Anc_cnd),
        )