from ducktools.classbuilder import SlotFields, make_field_gatherer, make_slot_gatherer, get_flags
from ducktools.classbuilder.prefab import attribute, Attribute, Prefab, prefab, get_attributes


slot_gatherer = make_slot_gatherer(field_type=Attribute)
attrib_gatherer = make_field_gatherer(field_type=Attribute, leave_default_values=True)

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

        assert AnnotationsNotGathered.c == 42

        assert get_attributes(AnnotationsNotGathered) == {'c': attribute(default=42)}

        assert get_flags(AnnotationsNotGathered)['gatherer'] == attrib_gatherer

    def test_baseclass(self):
        @prefab(gatherer=attrib_gatherer)
        class AnnotationsNotGathered:
            a: int
            b: str
            c: int = attribute(default=42)

        ex = AnnotationsNotGathered()
        assert not hasattr(ex, 'a')
        assert not hasattr(ex, 'b')
        assert ex.c == 42

        assert AnnotationsNotGathered.c == 42

        assert get_attributes(AnnotationsNotGathered) == {'c': attribute(default=42)}
        assert get_flags(AnnotationsNotGathered)['gatherer'] == attrib_gatherer
