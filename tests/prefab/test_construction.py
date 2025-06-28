import pytest

from ducktools.classbuilder import get_fields
from ducktools.classbuilder.annotations import get_ns_annotations
from ducktools.classbuilder.prefab import build_prefab, prefab, attribute, PrefabError


from utils import graalpy_fails  # type: ignore


def test_build_basic_prefab():
    DynamicTestClass = build_prefab(
        "DynamicTestClass",
        [
            ("x", attribute()),
            ("y", attribute(default="test")),
        ],
    )

    assert list(get_fields(DynamicTestClass)) == ["x", "y"]

    inst = DynamicTestClass(12)
    inst_2 = DynamicTestClass(12)
    inst_3 = DynamicTestClass(10)

    assert inst.x == 12
    assert inst.y == "test"

    assert inst == inst_2
    assert inst != inst_3

    assert repr(inst) == "DynamicTestClass(x=12, y='test')"


def test_keep_dict_funcs():
    """defined methods in dict should be kept as they are in the class"""
    __match_args__ = ("x",)

    def __init__(self, x=0, y=0):
        self.x = 0
        self.y = 0

    def __repr__(self):
        return "ORIGINAL REPR"

    def __eq__(self, other):
        return False

    def __iter__(self):
        yield from ["ORIGINAL ITER"]

    method_dict = {
        "__match_args__": __match_args__,
        "__init__": __init__,
        "__repr__": __repr__,
        "__eq__": __eq__,
        "__iter__": __iter__,
    }

    KeepDefinedMethods = build_prefab(
        "KeepDefinedMethods",
        [("x", attribute(default=-1)), ("y", attribute(default=-1))],
        bases=(),
        class_dict=method_dict,
        iter=True,
        match_args=True,
    )

    x = KeepDefinedMethods(42)

    assert x.x == 0
    assert repr(x) == "ORIGINAL REPR"
    assert x != x
    assert list(x)[0] == "ORIGINAL ITER"
    assert KeepDefinedMethods.__match_args__ == ("x",)


def test_double_decorate():
    with pytest.raises(
        PrefabError,
        match="Decorated class 'DoubleDecorated' has already been processed as a Prefab.",
    ):

        @prefab
        @prefab
        class DoubleDecorated:
            pass


def test_kwonly_class():

    # This class should actually work because *all* attributes are kw_only
    @prefab(kw_only=True)
    class KeywordPrefab:
        a: int = 0
        b: int = attribute(kw_only=True)
        c: int = attribute()  # kw_only should be ignored


@graalpy_fails
def test_build_slotted():
    SlottedClass = build_prefab(
        "SlottedClass",
        [
            ("x", attribute(doc="x co-ordinate", type=float)),
            ("y", attribute(default=0, doc="y co-ordinate", type=float))
        ],
        slots=True,
    )

    inst = SlottedClass(1)
    assert inst.x == 1
    assert inst.y == 0
    assert SlottedClass.__slots__ == {'x': "x co-ordinate", 'y': "y co-ordinate"}

    assert get_ns_annotations(SlottedClass.__dict__) == {'x': float, 'y': float}

    # Test slots are functioning
    with pytest.raises(AttributeError):
        inst.z = 0
