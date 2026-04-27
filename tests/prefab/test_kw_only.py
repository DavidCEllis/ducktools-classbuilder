import pytest

from ducktools.classbuilder.annotations import get_ns_annotations
from ducktools.classbuilder.prefab import KW_ONLY, Prefab, attribute, prefab


def test_kw_only_basic():
    @prefab
    class KWBasic:
        x = attribute(kw_only=True)
        y = attribute(kw_only=True)

    # Check the typeerror is raised for
    # trying to use positional arguments
    with pytest.raises(TypeError):
        x = KWBasic(1, 2)

    x = KWBasic(x=1, y=2)
    assert (x.x, x.y) == (1, 2)


def test_kw_only_ordering():
    # Test the kw_only argument is not also positional
    @prefab
    class KWOrdering:
        x = attribute(default=2, kw_only=True)
        y = attribute()

    with pytest.raises(TypeError):
        x = KWOrdering(1, 2)

    x = KWOrdering(1)
    assert (x.x, x.y) == (2, 1)
    assert repr(x).endswith("KWOrdering(x=2, y=1)")



def test_on_attribute():
    @prefab
    class KWBase:
        x = attribute(default=2, kw_only=True)

    @prefab
    class KWChild(KWBase):
        y = attribute()

    with pytest.raises(TypeError):
        x = KWChild(1, 2)

    x = KWChild(x=2, y=1)
    y = KWChild(1)
    assert (x.x, x.y) == (2, 1)
    assert x == y
    assert repr(x).endswith("KWChild(x=2, y=1)")


class TestKWOnlyClassArg:
    def test_kw_only_prefab_argument(self):
        @prefab(kw_only=True)
        class KWPrefabArgument:
            x = attribute()
            y = attribute()

        with pytest.raises(TypeError):
            x = KWPrefabArgument(1, 2)

        x = KWPrefabArgument(x=1, y=2)

        assert (x.x, x.y) == (1, 2)
        assert repr(x).endswith("KWPrefabArgument(x=1, y=2)")

    def test_kw_only_prefab_argument_overrides(self):
        @prefab(kw_only=True)
        class KWPrefabArgumentOverrides:
            x = attribute()
            y = attribute(kw_only=False)

        with pytest.raises(TypeError):
            x = KWPrefabArgumentOverrides(1, 2)

        x = KWPrefabArgumentOverrides(x=1, y=2)

        assert (x.x, x.y) == (1, 2)
        assert repr(x).endswith("KWPrefabArgumentOverrides(x=1, y=2)")

    def test_only_applies_to_new_fields(self):
        @prefab
        class Base:
            name: str = "Dent"

        @prefab(kw_only=True)
        class Sub(Base):
            answer: int = 42

        with pytest.raises(TypeError):
            _ = Sub("Zaphod", 24)

        ex = Sub("Zaphod", answer=54)
        assert ex.name == "Zaphod"
        assert ex.answer == 54

    def test_ignored_by_new_subclass(self):
        @prefab(kw_only=True)
        class Base:
            name: str = "Dent"

        @prefab
        class Sub(Base):
            answer: int = 42

        with pytest.raises(TypeError):
            _ = Sub("Zaphod", 24)

        ex = Sub(54, name="Zaphod")

        assert ex.name == "Zaphod"
        assert ex.answer == 54

    def test_inherited_in_class_form(self):
        # The base class version should inherit kw_only
        class Base(Prefab, kw_only=True):
            name: str = "Dent"

        class Sub(Base):
            answer: int = 42

        with pytest.raises(TypeError):
            _ = Sub("Zaphod", 24)

        with pytest.raises(TypeError):
            _ = Sub(24, name="Zaphod")

        ex = Sub(name="Zaphod", answer=54)
        assert ex.name == "Zaphod"
        assert ex.answer == 54


def test_kw_flag_no_defaults():
    @prefab
    class KWFlagNoDefaults:
        x: int
        _: KW_ONLY  # type: ignore
        y: int

    annotations = get_ns_annotations(KWFlagNoDefaults.__dict__)

    assert "_" in annotations

    with pytest.raises(TypeError):
        x = KWFlagNoDefaults(1, 2)

    x = KWFlagNoDefaults(x=1, y=2)

    assert not hasattr(x, "_")

    assert (x.x, x.y) == (1, 2)
    assert repr(x).endswith("KWFlagNoDefaults(x=1, y=2)")


def test_kw_flat_defaults():
    @prefab
    class KWFlagXDefault:
        x: int = 1
        _: KW_ONLY  # type: ignore
        y: int  # type: ignore

    with pytest.raises(TypeError):
        x = KWFlagXDefault(1, 2)

    x = KWFlagXDefault(y=2)
    y = KWFlagXDefault(1, y=2)

    assert (x.x, x.y) == (1, 2)
    assert x == y
    assert repr(x).endswith("KWFlagXDefault(x=1, y=2)")
