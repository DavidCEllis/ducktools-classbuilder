from ducktools.classbuilder import META_GATHERER_NAME, SlotFields, make_field_gatherer, make_slot_gatherer, get_flags
from ducktools.classbuilder.prefab import attribute, Attribute, Prefab, prefab, get_attributes


slot_gatherer = make_slot_gatherer(field_type=Attribute)
attrib_gatherer = make_field_gatherer(field_type=Attribute, leave_default_values=False)

class TestUsesGatherer:
    def test_decorator(self):
        @prefab(gatherer=slot_gatherer)
        class SlotGathered:
            __slots__ = SlotFields(a=42)

        assert SlotGathered().a == 42
        assert get_attributes(SlotGathered) == {'a': Attribute(default=42)}


    def test_baseclass(self):
        class SlotGathered(Prefab, gatherer=slot_gatherer):
            __slots__ = SlotFields(a=42)

        assert SlotGathered().a == 42
        assert get_attributes(SlotGathered) == {'a': Attribute(default=42)}


class TestIgnoresAnnotations:
    def test_decorator(self):
        @prefab(gatherer=attrib_gatherer)
        class AnnotationsNotGathered:
            a: int
            b: str
            c: int = attribute(default=42)

        ex = AnnotationsNotGathered()
        assert not hasattr(ex, 'a')
        assert not hasattr(ex, 'b')
        assert ex.c == 42

        assert get_attributes(AnnotationsNotGathered) == {'c': attribute(default=42)}

    def test_baseclass(self):
        class AnnotationsNotGathered(Prefab, gatherer=attrib_gatherer):
            a: int
            b: str
            c: int = attribute(default=42)

        ex = AnnotationsNotGathered()
        assert not hasattr(ex, 'a')
        assert not hasattr(ex, 'b')
        assert ex.c == 42

        assert get_attributes(AnnotationsNotGathered) == {'c': attribute(default=42)}

        # Base class examples keep the meta gatherer
        assert getattr(AnnotationsNotGathered, META_GATHERER_NAME) == attrib_gatherer

        # Check the meta gatherer is preserved in a subclass
        class AnnotationsNotGatheredSub(AnnotationsNotGathered):
            d: int
            e: str
            f: int = attribute(default=314)

        assert getattr(AnnotationsNotGatheredSub, META_GATHERER_NAME) == attrib_gatherer

        assert get_attributes(AnnotationsNotGatheredSub) == {'c': attribute(default=42), 'f': attribute(default=314)}
