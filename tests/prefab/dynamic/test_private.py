from ducktools.classbuilder.prefab import Prefab, attribute, get_attributes


def test_private_attribute():
    class Ex(Prefab):
        _internal: "str | None" = attribute(default=None, private=True)
        a: int
        b: str


    ex = Ex(1, "Hello")

    assert ex.a == 1
    assert ex.b == "Hello"

    assert ex._internal is None

    _internal_attrib = get_attributes(Ex)["_internal"]

    assert _internal_attrib.init is False
    assert _internal_attrib.repr is False
    assert _internal_attrib.iter is False
    assert _internal_attrib.compare is False
    assert _internal_attrib.serialize is False
