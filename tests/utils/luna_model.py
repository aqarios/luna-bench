from pathlib import Path

from luna_model import Model, TranslationTarget, Variable


def simple_model(name: str) -> Model:
    model = Model(name)
    with model.environment:
        x = Variable("x")
        y = Variable("y")
    model.objective = x * y + x
    model.constraints += x >= 0
    model.constraints += y <= 5

    return model


def write_model_file(
    directory: Path,
    stem: str,
    suffix: str = ".mps",
    internal_name: str = "name_inside_the_file",
) -> Path:
    """Write a model file into ``directory`` and return its path.

    The name stored *inside* the file deliberately differs from the file stem so
    tests can tell which of the two a loaded model is named after.
    """
    path = directory / f"{stem}{suffix}"
    model = simple_model(internal_name)
    if suffix == ".lp":
        model.to(TranslationTarget.LP, filepath=path)
    else:
        model.to(TranslationTarget.MPS, filepath=path)
    return path


def write_encoded_model_file(
    directory: Path,
    stem: str,
    suffix: str = ".bin",
    internal_name: str = "name_inside_the_file",
) -> Path:
    """Write a model in the compact binary format and return its path.

    ``Model.from_`` cannot read this - only ``Model.decode`` can - so it covers
    the fallback taken for a suffix ``from_`` does not recognise.
    """
    path = directory / f"{stem}{suffix}"
    path.write_bytes(simple_model(internal_name).encode())
    return path
