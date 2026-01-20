from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from luna_quantum import Vtype

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.components.helper.degree import ConstraintDegree
from luna_bench.components.helper.model_matrix_extraction import ModelMatrix
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper
from luna_bench.helpers import feature

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
    mean_var_node_degree_cont : float
        Mean node degree for continuous variables.
    median_var_node_degree_cont : float
        Median node degree for continuous variables.
    vc_var_node_degree_cont : float
        Variation coefficient of node degrees for continuous variables.
    q90_var_node_degree_cont : float
        90th percentile of node degrees for continuous variables.
    q10_var_node_degree_cont : float
        10th percentile of node degrees for continuous variables.
    mean_var_node_degree_non_cont : float
        Mean node degree for non-continuous variables.
    median_var_node_degree_non_cont : float
        Median node degree for non-continuous variables.
    vc_var_node_degree_non_cont : float
        Variation coefficient of node degrees for non-continuous variables.
    q90_var_node_degree_non_cont : float
        90th percentile of node degrees for non-continuous variables.
    q10_var_node_degree_non_cont : float
        10th percentile of node degrees for non-continuous variables.
    mean_var_node_degree_all : float
        Mean node degree for all variables.
    median_var_node_degree_all : float
        Median node degree for all variables.
    vc_var_node_degree_all : float
        Variation coefficient of node degrees for all variables.
    q90_var_node_degree_all : float
        90th percentile of node degrees for all variables.
    q10_var_node_degree_all : float
        10th percentile of node degrees for all variables.
    mean_cons_node_degree : float
        Mean node degree for all constraints.
    median_cons_node_degree : float
        Median node degree for all constraints.
    vc_cons_node_degree : float
        Variation coefficient of constraint node degrees.
    q90_cons_node_degree : float
        90th percentile of constraint node degrees.
    q10_cons_node_degree : float
        10th percentile of constraint node degrees.
    mean_cons_node_degree_cont : float
        Mean node degree for continuous constraints.
    median_cons_node_degree_cont : float
        Median node degree for continuous constraints.
    vc_cons_node_degree_cont : float
        Variation coefficient of node degrees for continuous constraints.
    q90_cons_node_degree_cont : float
        90th percentile of node degrees for continuous constraints.
    q10_cons_node_degree_cont : float
        10th percentile of node degrees for continuous constraints.
    mean_cons_node_degree_non_cont : float
        Mean node degree for non-continuous constraints.
    median_cons_node_degree_non_cont : float
        Median node degree for non-continuous constraints.
    vc_cons_node_degree_non_cont : float
        Variation coefficient of node degrees for non-continuous constraints.
    q90_cons_node_degree_non_cont : float
        90th percentile of node degrees for non-continuous constraints.
    q10_cons_node_degree_non_cont : float
        10th percentile of node degrees for non-continuous constraints.
    """

    # Variable node degree statistics - continuous
    mean_var_node_degree_cont: float
    median_var_node_degree_cont: float
    vc_var_node_degree_cont: float
    q90_var_node_degree_cont: float
    q10_var_node_degree_cont: float

    # Variable node degree statistics - non-continuous
    mean_var_node_degree_non_cont: float
    median_var_node_degree_non_cont: float
    vc_var_node_degree_non_cont: float
    q90_var_node_degree_non_cont: float
    q10_var_node_degree_non_cont: float

    # Variable node degree statistics - all
    mean_var_node_degree_all: float
    median_var_node_degree_all: float
    vc_var_node_degree_all: float
    q90_var_node_degree_all: float
    q10_var_node_degree_all: float

    # Constraint node degree statistics - all
    mean_cons_node_degree: float
    median_cons_node_degree: float
    vc_cons_node_degree: float
    q90_cons_node_degree: float
    q10_cons_node_degree: float

    # Constraint node degree statistics - continuous
    mean_cons_node_degree_cont: float
    median_cons_node_degree_cont: float
    vc_cons_node_degree_cont: float
    q90_cons_node_degree_cont: float
    q10_cons_node_degree_cont: float

    # Constraint node degree statistics - non-continuous
    mean_cons_node_degree_non_cont: float
    median_cons_node_degree_non_cont: float
    vc_cons_node_degree_non_cont: float
    q90_cons_node_degree_non_cont: float
    q10_cons_node_degree_non_cont: float


@feature
class VariableConstraintGraphFeatures(IFeature):
    """
    Feature extractor for variable-constraint graph properties.

    Calculates node degree statistics for variables and constraints in the
    bipartite graph representation of an optimization model. Computes statistics
    separately for continuous and non-continuous variables/constraints.
    """

    def run(self, model: Model) -> VariableConstraintGraphFeaturesResult:
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
        ac, _ = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=Vtype.Real)
        ac_binary = (ac != 0).astype(int)
        ac_vnd = np.sum(ac_binary, axis=0)
        ac_cnd = np.sum(ac_binary, axis=1)

        # Non-continuous
        anc, _ = ModelMatrix.constraint_matrix(
            model, degree=ConstraintDegree.LINEAR, vtype=[Vtype.Integer, Vtype.Binary]
        )
        anc_binary = (anc != 0).astype(int)
        anc_vnd = np.sum(anc_binary, axis=0)
        anc_cnd = np.sum(anc_binary, axis=1)

        # all variables
        av, _ = ModelMatrix.constraint_matrix(model, degree=ConstraintDegree.LINEAR, vtype=None)
        av_binary = (av != 0).astype(int)
        av_vnd = np.sum(av_binary, axis=0)
        av_cnd = np.sum(av_binary, axis=1)

        return VariableConstraintGraphFeaturesResult(
            # var continuous
            mean_var_node_degree_cont=NumpyStatsHelper.mean(ac_vnd),
            median_var_node_degree_cont=NumpyStatsHelper.median(ac_vnd),
            vc_var_node_degree_cont=NumpyStatsHelper.vc(ac_vnd),
            q90_var_node_degree_cont=NumpyStatsHelper.q90(ac_vnd),
            q10_var_node_degree_cont=NumpyStatsHelper.q10(ac_vnd),
            # var non-continuous
            mean_var_node_degree_non_cont=NumpyStatsHelper.mean(anc_vnd),
            median_var_node_degree_non_cont=NumpyStatsHelper.median(anc_vnd),
            vc_var_node_degree_non_cont=NumpyStatsHelper.vc(anc_vnd),
            q90_var_node_degree_non_cont=NumpyStatsHelper.q90(anc_vnd),
            q10_var_node_degree_non_cont=NumpyStatsHelper.q10(anc_vnd),
            # var all types vars
            mean_var_node_degree_all=NumpyStatsHelper.mean(av_vnd),
            median_var_node_degree_all=NumpyStatsHelper.median(av_vnd),
            vc_var_node_degree_all=NumpyStatsHelper.vc(av_vnd),
            q90_var_node_degree_all=NumpyStatsHelper.q90(av_vnd),
            q10_var_node_degree_all=NumpyStatsHelper.q10(av_vnd),
            # cons all types
            mean_cons_node_degree=NumpyStatsHelper.mean(av_cnd),
            median_cons_node_degree=NumpyStatsHelper.median(av_cnd),
            vc_cons_node_degree=NumpyStatsHelper.vc(av_cnd),
            q90_cons_node_degree=NumpyStatsHelper.q90(av_cnd),
            q10_cons_node_degree=NumpyStatsHelper.q10(av_cnd),
            # cons continuous
            mean_cons_node_degree_cont=NumpyStatsHelper.mean(ac_cnd),
            median_cons_node_degree_cont=NumpyStatsHelper.median(ac_cnd),
            vc_cons_node_degree_cont=NumpyStatsHelper.vc(ac_cnd),
            q90_cons_node_degree_cont=NumpyStatsHelper.q90(ac_cnd),
            q10_cons_node_degree_cont=NumpyStatsHelper.q10(ac_cnd),
            # cons non-continuous
            mean_cons_node_degree_non_cont=NumpyStatsHelper.mean(anc_cnd),
            median_cons_node_degree_non_cont=NumpyStatsHelper.median(anc_cnd),
            vc_cons_node_degree_non_cont=NumpyStatsHelper.vc(anc_cnd),
            q90_cons_node_degree_non_cont=NumpyStatsHelper.q90(anc_cnd),
            q10_cons_node_degree_non_cont=NumpyStatsHelper.q10(anc_cnd),
        )
