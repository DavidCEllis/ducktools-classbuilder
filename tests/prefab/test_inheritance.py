"""Tests that Prefabs handle inheritance as expected"""

import pytest

from ducktools.classbuilder.prefab import attribute, prefab


# Class Definitions
@prefab
class Coordinate:
    x: float
    y: float


@prefab
class Coordinate3D(Coordinate):
    z = attribute()


@prefab
class CoordinateTime:
    t = attribute()


@prefab
class Coordinate4D(CoordinateTime, Coordinate3D):
    pass


@prefab
class BasePreInitPostInit:
    def __prefab_pre_init__(self):
        self.pre_init = True

    def __prefab_post_init__(self):
        self.post_init = True


@prefab
class ChildPreInitPostInit(BasePreInitPostInit):
    pass


# Multiple inheritance inconsistency test classes
# classvar and field should be equal
@prefab
class Base:
    field: int = 10
    classvar = 10


@prefab
class Child1(Base):
    pass


@prefab
class Child2(Base):
    field: int = 50
    classvar = 50


@prefab
class GrandChild(Child1, Child2):
    pass


# Tests
def test_basic_inheritance():
    x = Coordinate3D(1, 2, 3)

    assert (x.x, x.y, x.z) == (1, 2, 3)


def test_layered_inheritance():
    x = Coordinate4D(1, 2, 3, 4)

    assert x.PREFAB_FIELDS == ["x", "y", "z", "t"]

    assert (x.x, x.y, x.z, x.t) == (1, 2, 3, 4)


def test_inherited_pre_post_init():
    # Inherited pre/post init functions should be used
    base_ex = BasePreInitPostInit()
    assert base_ex.pre_init
    assert base_ex.post_init

    inherit_ex = ChildPreInitPostInit()
    assert inherit_ex.pre_init
    assert inherit_ex.post_init


def test_mro_correct():
    ex = GrandChild()

    assert ex.field == ex.classvar


def test_two_fields_one_default():
    # Incorrect default argument order should still fail
    # even with inheritance
    with pytest.raises(SyntaxError):
        @prefab
        class B:
            x: int = 0


        @prefab
        class C(B):
            y: int  # type: ignore


    with pytest.raises(SyntaxError):
        @prefab
        class B:
            x: int
            y: int


        @prefab
        class C(B):
            x: int = 2
