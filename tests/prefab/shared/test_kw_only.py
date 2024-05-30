import pytest

from ducktools.classbuilder.annotations import get_ns_annotations

def test_kw_only_basic():
    from kw_only import KWBasic

    # Check the typeerror is raised for
    # trying to use positional arguments
    with pytest.raises(TypeError):
        x = KWBasic(1, 2)

    x = KWBasic(x=1, y=2)
    assert (x.x, x.y) == (1, 2)


def test_kw_only_ordering():
    from kw_only import KWOrdering

    with pytest.raises(TypeError):
        x = KWOrdering(1, 2)

    x = KWOrdering(1)
    assert (x.x, x.y) == (2, 1)
    assert repr(x) == "KWOrdering(x=2, y=1)"


def test_kw_only_inheritance():
    from kw_only import KWChild

    with pytest.raises(TypeError):
        x = KWChild(1, 2)

    x = KWChild(x=2, y=1)
    y = KWChild(1)
    assert (x.x, x.y) == (2, 1)
    assert x == y
    assert repr(x) == "KWChild(x=2, y=1)"


def test_kw_only_prefab_argument():
    from kw_only import KWPrefabArgument

    with pytest.raises(TypeError):
        x = KWPrefabArgument(1, 2)

    x = KWPrefabArgument(x=1, y=2)

    assert (x.x, x.y) == (1, 2)
    assert repr(x) == "KWPrefabArgument(x=1, y=2)"


def test_kw_only_prefab_argument_overrides():
    from kw_only import KWPrefabArgumentOverrides

    with pytest.raises(TypeError):
        x = KWPrefabArgumentOverrides(1, 2)

    x = KWPrefabArgumentOverrides(x=1, y=2)

    assert (x.x, x.y) == (1, 2)
    assert repr(x) == "KWPrefabArgumentOverrides(x=1, y=2)"


def test_kw_flag_no_defaults():
    from kw_only import KWFlagNoDefaults

    annotations = get_ns_annotations(KWFlagNoDefaults.__dict__)

    assert "_" in annotations

    with pytest.raises(TypeError):
        x = KWFlagNoDefaults(1, 2)

    x = KWFlagNoDefaults(x=1, y=2)

    assert not hasattr(x, "_")

    assert (x.x, x.y) == (1, 2)
    assert repr(x) == "KWFlagNoDefaults(x=1, y=2)"


def test_kw_flat_defaults():
    from kw_only import KWFlagXDefault

    with pytest.raises(TypeError):
        x = KWFlagXDefault(1, 2)

    x = KWFlagXDefault(y=2)
    y = KWFlagXDefault(1, y=2)

    assert (x.x, x.y) == (1, 2)
    assert x == y
    assert repr(x) == "KWFlagXDefault(x=1, y=2)"
