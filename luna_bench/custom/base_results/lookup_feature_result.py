from .feature_result import FeatureResult


class LookupFeatureResult[TValue](FeatureResult):
    """
    Result of a `BaseValueLookupFeature`: the value assigned to the model.

    Attributes
    ----------
    value : TValue
        The value registered for this model. Its type is fixed by the concrete
        feature subclass, which also validates it.
    """

    value: TValue
