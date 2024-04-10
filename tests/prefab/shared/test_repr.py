def test_basic_repr():
    from repr_func import RegularRepr

    x = RegularRepr()
    assert repr(x) == "RegularRepr(x='Hello', y='World')"


def test_basic_repr_no_fields():
    from repr_func import NoReprAttributes

    x = NoReprAttributes()
    assert repr(x) == "<prefab NoReprAttributes>"


def test_one_attribute_no_repr():
    from repr_func import OneAttributeNoRepr

    x = OneAttributeNoRepr()
    assert repr(x) == "<prefab OneAttributeNoRepr; y='World'>"


def test_one_attribute_no_init():
    from repr_func import OneAttributeNoInit

    x = OneAttributeNoInit()
    assert repr(x) == "<prefab OneAttributeNoInit; x='Hello', y='World'>"


def test_one_attribute_exclude_field():
    from repr_func import OneAttributeExcludeField

    x = OneAttributeExcludeField()
    assert repr(x) == "<prefab OneAttributeExcludeField; x='Hello'>"


def test_regular_one_arg():
    from repr_func import RegularReprOneArg

    x = RegularReprOneArg()
    assert repr(x) == "RegularReprOneArg(x='Hello')"


def test_recursive():
    from repr_func import RecursiveObject

    ex = RecursiveObject()
    ex.x = ex

    assert repr(ex) == "RecursiveObject(x=...)"
