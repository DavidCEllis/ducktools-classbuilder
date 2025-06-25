from ducktools.classbuilder.prefab import prefab, attribute
from ducktools.classbuilder import INTERNALS_DICT


def test_internals_dict():
    @prefab
    class X:
        x: int
        y: int = 2

    @prefab
    class Z(X):
        z: int = 3

    x_attrib = attribute(type=int)
    y_attrib = attribute(default=2, type=int)
    z_attrib = attribute(default=3, type=int)

    assert hasattr(X, INTERNALS_DICT)

    x_internals = getattr(X, INTERNALS_DICT)
    assert x_internals["fields"] == x_internals["local_fields"]
    assert x_internals["fields"] == {"x": x_attrib, "y": y_attrib}

    z_internals = getattr(Z, INTERNALS_DICT)
    assert z_internals["fields"] != z_internals["local_fields"]
    assert z_internals["fields"] == {"x": x_attrib, "y": y_attrib, "z": z_attrib}
