from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Vtype

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature

from .utils import constraint_matrix, mean, median, q10, q90, vc

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
        ac = constraint_matrix(model, degree=1, vtype=Vtype.Real)
        ac_binary = (ac != 0).astype(int)
        ac_vnd = np.sum(ac_binary, axis=0)  # Variable node degrees
        ac_cnd = np.sum(ac_binary, axis=1)  # Constraint node degrees

        # Non-continuous
        anc = constraint_matrix(model, degree=1, vtype=[Vtype.Integer, Vtype.Binary])
        anc_binary = (anc != 0).astype(int)
        anc_vnd = np.sum(anc_binary, axis=0)
        anc_cnd = np.sum(anc_binary, axis=1)

        # all variables
        av = constraint_matrix(model, degree=1, vtype=None)
        av_binary = (av != 0).astype(int)
        av_vnd = np.sum(av_binary, axis=0)
        av_cnd = np.sum(av_binary, axis=1)

        return VariableConstraintGraphFeaturesResult(
            # Variable node degree statistics - continuous
            mean_variable_node_degree_continuous=mean(ac_vnd),
            median_variable_node_degree_continuous=median(ac_vnd),
            vc_variable_node_degree_continuous=vc(ac_vnd),
            q90_variable_node_degree_continuous=q90(ac_vnd),
            q10_variable_node_degree_continuous=q10(ac_vnd),
            # Variable node degree statistics - non-continuous
            mean_variable_node_degree_non_continuous=mean(anc_vnd),
            median_variable_node_degree_non_continuous=median(anc_vnd),
            vc_variable_node_degree_non_continuous=vc(anc_vnd),
            q90_variable_node_degree_non_continuous=q90(anc_vnd),
            q10_variable_node_degree_non_continuous=q10(anc_vnd),
            # Variable node degree statistics - all
            mean_variable_node_degree_all=mean(av_vnd),
            median_variable_node_degree_all=median(av_vnd),
            vc_variable_node_degree_all=vc(av_vnd),
            q90_variable_node_degree_all=q90(av_vnd),
            q10_variable_node_degree_all=q10(av_vnd),
            # Constraint node degree statistics - all
            mean_constraint_node_degree=mean(av_cnd),
            median_constraint_node_degree=median(av_cnd),
            vc_constraint_node_degree=vc(av_cnd),
            q90_constraint_node_degree=q90(av_cnd),
            q10_constraint_node_degree=q10(av_cnd),
            # Constraint node degree statistics - continuous
            mean_constraint_node_degree_continuous=mean(ac_cnd),
            median_constraint_node_degree_continuous=median(ac_cnd),
            vc_constraint_node_degree_continuous=vc(ac_cnd),
            q90_constraint_node_degree_continuous=q90(ac_cnd),
            q10_constraint_node_degree_continuous=q10(ac_cnd),
            # Constraint node degree statistics - non-continuous
            mean_constraint_node_degree_non_continuous=mean(anc_cnd),
            median_constraint_node_degree_non_continuous=median(anc_cnd),
            vc_constraint_node_degree_non_continuous=vc(anc_cnd),
            q90_constraint_node_degree_non_continuous=q90(anc_cnd),
            q10_constraint_node_degree_non_continuous=q10(anc_cnd),
        )
