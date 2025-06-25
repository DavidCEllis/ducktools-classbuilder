import pytest

from ducktools.classbuilder.annotations import get_ns_annotations
from ducktools.classbuilder.prefab import attribute, prefab, KW_ONLY


# Test Classes
@prefab
class KWBasic:
    x = attribute(kw_only=True)
    y = attribute(kw_only=True)


@prefab
class KWOrdering:
    x = attribute(default=2, kw_only=True)
    y = attribute()


@prefab
class KWBase:
    x = attribute(default=2, kw_only=True)


@prefab
class KWChild(KWBase):
    y = attribute()


@prefab(kw_only=True)
class KWPrefabArgument:
    x = attribute()
    y = attribute()


@prefab(kw_only=True)
class KWPrefabArgumentOverrides:
    x = attribute()
    y = attribute(kw_only=False)


@prefab
class KWFlagNoDefaults:
    x: int
    _: KW_ONLY  # type: ignore
    y: int


@prefab
class KWFlagXDefault:
    x: int = 1
    _: KW_ONLY  # type: ignore
    y: int  # type: ignore


def test_kw_only_basic():
    # Check the typeerror is raised for
    # trying to use positional arguments
    with pytest.raises(TypeError):
        x = KWBasic(1, 2)

    x = KWBasic(x=1, y=2)
    assert (x.x, x.y) == (1, 2)


def test_kw_only_ordering():
    with pytest.raises(TypeError):
        x = KWOrdering(1, 2)

    x = KWOrdering(1)
    assert (x.x, x.y) == (2, 1)
    assert repr(x) == "KWOrdering(x=2, y=1)"


def test_kw_only_inheritance():
    with pytest.raises(TypeError):
        x = KWChild(1, 2)

    x = KWChild(x=2, y=1)
    y = KWChild(1)
    assert (x.x, x.y) == (2, 1)
    assert x == y
    assert repr(x) == "KWChild(x=2, y=1)"


def test_kw_only_prefab_argument():
    with pytest.raises(TypeError):
        x = KWPrefabArgument(1, 2)

    x = KWPrefabArgument(x=1, y=2)

    assert (x.x, x.y) == (1, 2)
    assert repr(x) == "KWPrefabArgument(x=1, y=2)"


def test_kw_only_prefab_argument_overrides():
    with pytest.raises(TypeError):
        x = KWPrefabArgumentOverrides(1, 2)

    x = KWPrefabArgumentOverrides(x=1, y=2)

    assert (x.x, x.y) == (1, 2)
    assert repr(x) == "KWPrefabArgumentOverrides(x=1, y=2)"


def test_kw_flag_no_defaults():
    annotations = get_ns_annotations(KWFlagNoDefaults.__dict__)

    assert "_" in annotations

    with pytest.raises(TypeError):
        x = KWFlagNoDefaults(1, 2)

    x = KWFlagNoDefaults(x=1, y=2)

    assert not hasattr(x, "_")

    assert (x.x, x.y) == (1, 2)
    assert repr(x) == "KWFlagNoDefaults(x=1, y=2)"


def test_kw_flat_defaults():
    with pytest.raises(TypeError):
        x = KWFlagXDefault(1, 2)

    x = KWFlagXDefault(y=2)
    y = KWFlagXDefault(1, y=2)

    assert (x.x, x.y) == (1, 2)
    assert x == y
    assert repr(x) == "KWFlagXDefault(x=1, y=2)"
