from reannotate import DeferredAnnotation
from ducktools.classbuilder import Field, replace


def test_replace_preserves_type():
    # Test that the Field __replace__ method preserves the internal _type

    f = Field(type=DeferredAnnotation(str))

    assert f.type is str
    assert f._type == DeferredAnnotation(str)

    new_f = replace(f)

    assert new_f.type is str
    assert new_f._type == DeferredAnnotation(str)
