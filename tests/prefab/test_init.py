"""Tests for the behaviour of __init__"""

import sys
from pathlib import Path
from typing import Union

import pytest

from ducktools.classbuilder.prefab import prefab, attribute


# Classes for tests
@prefab
class Coordinate:
    x: float
    y: float


@prefab
class CoordinateFixedY:
    x = attribute()
    y = attribute(default=2, init=False)


@prefab
class CoordinateDefaults:
    x = attribute(default=0)
    y = attribute(default=0)


@prefab
class MutableDefault:
    x = attribute(default=list())  # type: ignore


@prefab
class FactoryDefault:
    x = attribute(default_factory=list)  # type: ignore


@prefab
class Settings:
    """
    Global persistent settings handler
    """

    output_file = attribute(default=Path("Settings.json"))


@prefab
class PreInitExample:
    init_value: bool = True

    def __prefab_pre_init__(self):
        self.pre_init_ran = True


@prefab
class PostInitExample:
    init_value: bool = True

    def __prefab_post_init__(self):
        self.post_init_ran = True


@prefab
class PrePostInitArguments:
    x: int = 1
    y: int = 2

    def __prefab_pre_init__(self, x, y):
        if x > y:
            raise ValueError("X must be less than Y")

    def __prefab_post_init__(self, x, y):
        self.x = 2 * x
        self.y = 3 * y


@prefab
class ExcludeField:
    x = attribute(default="excluded_field", exclude_field=True)

    def __prefab_post_init__(self, x):
        self.x = x.upper()


@prefab
class PostInitPartial:
    x: int
    y: int
    z: "list[int]" = attribute(default_factory=list)

    def __prefab_post_init__(self, z):
        z.append(1)
        self.z = z


@prefab
class PostInitAnnotations:
    x: int
    y: Path

    def __prefab_post_init__(self, y: Union[str, Path]):
        self.y = Path(y)


@prefab
class EmptyContainers:
    x: list = attribute(default_factory=list)
    y: set = attribute(default_factory=set)
    z: dict = attribute(default_factory=dict)


@prefab
class TypeSignatureInit:
    x: int
    y: str = "Test"


@prefab
class PartialTypeSignatureInit:
    x = attribute()
    y: str = attribute(default="Test")


# Tests
def test_basic():
    x = Coordinate(1, 2)

    assert (x.x, x.y) == (1, 2)


def test_basic_kwargs():
    x = Coordinate(x=1, y=2)

    assert (x.x, x.y) == (1, 2)


def test_init_exclude():
    x = CoordinateFixedY(x=1)
    assert (x.x, x.y) == (1, 2)


def test_basic_with_defaults():
    x = CoordinateDefaults()
    assert (x.x, x.y) == (0, 0)

    y = CoordinateDefaults(y=5)
    assert (y.x, y.y) == (0, 5)


def test_mutable_defaults_bad():
    """Test mutable defaults behave as they would in a regular class"""

    mut1 = MutableDefault()
    mut2 = MutableDefault()

    # Check the lists are the same object
    assert mut1.x is mut2.x


def test_default_factory_good():

    mut1 = FactoryDefault()
    mut2 = FactoryDefault()

    # Check the attribute is a list and is not the same list for different instances
    assert isinstance(mut1.x, list)
    assert mut1.x is not mut2.x


def test_no_default():
    with pytest.raises(TypeError) as e_info:
        x = Coordinate(1)

    error_message = (
        "Coordinate.__init__() missing 1 required positional argument: 'y'"
    )

    assert e_info.value.args[0] == error_message


def test_difficult_defaults():
    x = Settings()

    assert x.output_file == Path("Settings.json")


def test_pre_init():
    x = PreInitExample()
    assert hasattr(x, "pre_init_ran")


def test_post_init():
    x = PostInitExample()
    assert hasattr(x, "post_init_ran")


def test_pre_post_init_arguments():
    x = PrePostInitArguments()

    assert x.x == 2
    assert x.y == 6

    with pytest.raises(ValueError):
        y = PrePostInitArguments(2, 1)


def test_post_init_partial():
    x = PostInitPartial(1, 2)

    assert (x.x, x.y, x.z) == (1, 2, [1])


def test_post_init_annotations():
    x = PostInitAnnotations(1, "/usr/bin/python")

    init_annotations = PostInitAnnotations.__init__.__annotations__

    assert init_annotations["x"] == int
    assert init_annotations["y"] == Union[str, Path]


def test_exclude_field():
    x = ExcludeField()
    y = ExcludeField(x="still_excluded")

    assert x.x == "EXCLUDED_FIELD"
    assert y.x == "STILL_EXCLUDED"
    assert repr(x) == "<generated class ExcludeField>"
    assert repr(y) == "<generated class ExcludeField>"
    assert x == y


def test_replace_factory_default():
    mut1 = FactoryDefault(x=[1, 2, 3])
    assert mut1.x == [1, 2, 3]


def test_empty_containers_factory_default():
    # Empty containers should be copied and not replaced
    ec = EmptyContainers()
    assert ec.x == []
    assert ec.y == set()
    assert ec.z == {}

    empty_list = []
    empty_set = set()
    empty_dict = {}

    ec = EmptyContainers(empty_list, empty_set, empty_dict)

    assert ec.x is empty_list
    assert ec.y is empty_set
    assert ec.z is empty_dict


def test_signature():
    import inspect

    init_sig = inspect.signature(TypeSignatureInit.__init__)
    assert str(init_sig) == "(self, x: int, y: str = 'Test') -> None"


def test_partial_signature():
    import inspect

    init_sig = inspect.signature(PartialTypeSignatureInit.__init__)
    assert str(init_sig) == "(self, x, y: str = 'Test') -> None"


def test_inherited_signature():
    import inspect

    @prefab
    class Base:
        x: int
        y: str = "Base"

    class Inherited(Base):
        def __init__(self, x=42, y="Inherited") -> None:
            self.x = x
            self.y = y

    base_signature = inspect.signature(Base)
    inherited_signature = inspect.signature(Inherited)

    assert str(base_signature) == "(x: int, y: str = 'Base') -> None"
    assert str(inherited_signature) == "(x=42, y='Inherited') -> None"

    with pytest.raises(AttributeError):
        Base.__signature__

    with pytest.raises(AttributeError):
        Inherited.__signature__
