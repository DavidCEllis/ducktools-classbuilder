from ducktools.classbuilder.prefab import prefab, attribute


@prefab
class RegularRepr:
    x: str = "Hello"
    y: str = "World"


@prefab
class NoReprAttributes:
    x: str = attribute(default="Hello", repr=False)
    y: str = attribute(default="World", repr=False)


@prefab
class OneAttributeNoRepr:
    x: str = attribute(default="Hello", repr=False)
    y: str = "World"


@prefab
class OneAttributeNoInit:
    x: str = "Hello"
    y: str = attribute(default="World", init=False)


@prefab
class OneAttributeExcludeField:
    x: str = "Hello"
    y: str = attribute(default="World", exclude_field=True)

    def __prefab_post_init__(self, y):
        self.y = y


@prefab
class RegularReprOneArg:
    x: str = "Hello"
    y: str = attribute(default="World", init=False, repr=False)


@prefab(recursive_repr=True)
class RecursiveObject:
    x: "RecursiveObject | None" = None


# Actual tests
def test_basic_repr():
    x = RegularRepr()
    assert repr(x) == "RegularRepr(x='Hello', y='World')"


def test_basic_repr_no_fields():
    x = NoReprAttributes()
    assert repr(x) == "<generated class NoReprAttributes>"


def test_one_attribute_no_repr():
    x = OneAttributeNoRepr()
    assert repr(x) == "<generated class OneAttributeNoRepr; y='World'>"


def test_one_attribute_no_init():
    x = OneAttributeNoInit()
    assert repr(x) == "<generated class OneAttributeNoInit; x='Hello', y='World'>"


def test_one_attribute_exclude_field():
    x = OneAttributeExcludeField()
    assert repr(x) == "<generated class OneAttributeExcludeField; x='Hello'>"


def test_regular_one_arg():
    x = RegularReprOneArg()
    assert repr(x) == "RegularReprOneArg(x='Hello')"


def test_recursive():
    ex = RecursiveObject()
    ex.x = ex

    assert repr(ex) == "RecursiveObject(x=...)"
