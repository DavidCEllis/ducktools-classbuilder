# Some elements of annotationlib have been copied that are considered implementation details
# These tests are to make sure that the internals of annotations haven't changed in a way
# that breaks these elements.
# These tests should break if the internals change in such a way that they need to be updated

from annotationlib import Format, get_annotate_from_class_namespace
from ducktools.classbuilder.annotations.annotations_314 import _get_annotate_from_class_namespace


def test_annotate_retrieval():
    class Example:
        a: int
        b: str

    assert get_annotate_from_class_namespace(Example.__dict__) is _get_annotate_from_class_namespace(Example.__dict__)


def test_value_format():
    assert Format.VALUE == 1
