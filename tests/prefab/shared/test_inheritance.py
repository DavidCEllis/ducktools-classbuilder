"""Tests that Prefabs handle inheritance as expected"""

import pytest


def test_inherit_object():
    from inheritance import InheritObject

    x = InheritObject()
    y = InheritObject()

    assert x == y


def test_basic_inheritance():
    from inheritance import Coordinate3D

    x = Coordinate3D(1, 2, 3)

    assert (x.x, x.y, x.z) == (1, 2, 3)


def test_layered_inheritance():
    from inheritance import Coordinate4D

    x = Coordinate4D(1, 2, 3, 4)

    assert x.PREFAB_FIELDS == ["x", "y", "z", "t"]

    assert (x.x, x.y, x.z, x.t) == (1, 2, 3, 4)


def test_two_fields_one_default():
    # Incorrect default argument order should still fail
    # even with inheritance
    with pytest.raises(SyntaxError):
        import fails.inheritance_1

    with pytest.raises(SyntaxError):
        import fails.inheritance_2


def test_inherited_pre_post_init():
    # Inherited pre/post init functions should be used
    from inheritance import BasePreInitPostInit, ChildPreInitPostInit

    base_ex = BasePreInitPostInit()
    assert base_ex.pre_init
    assert base_ex.post_init

    inherit_ex = ChildPreInitPostInit()
    assert inherit_ex.pre_init
    assert inherit_ex.post_init


def test_mro_correct():
    from inheritance import GrandChild

    ex = GrandChild()

    assert ex.field == ex.classvar
