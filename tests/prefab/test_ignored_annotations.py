# Test that ignore_annotations truly does ignore the annotations
from ducktools.classbuilder.prefab import prefab, Prefab, attribute


def test_annotation_excluded():
    @prefab(ignore_annotations=True)
    class Example:
        a: int

    example = Example()

    assert not hasattr(example, 'a')

    class Example(Prefab, ignore_annotations=True):
        a: int

    example = Example()

    assert not hasattr(example, 'a')


def test_attribute_included():
    @prefab(ignore_annotations=True)
    class Example:
        a: int
        b: str = attribute()

    ex = Example("apple")

    assert ex.b == "apple"
    assert not hasattr(ex, 'a')

    class Example(Prefab, ignore_annotations=True):
        a: int
        b: str = attribute()

    ex = Example("apple")

    assert ex.b == "apple"
    assert not hasattr(ex, 'a')


def test_ignore_inherited():
    class Example(Prefab, ignore_annotations=True):
        a: int

    class ExampleSub(Example):
        b: str
        c: float = attribute()

    ex = ExampleSub(3.14)

    assert ex.c == 3.14
    assert not hasattr(ex, "a")
    assert not hasattr(ex, "b")


def test_ignore_not_inherited():
    @prefab(ignore_annotations=True)
    class Example:
        a: int

    @prefab
    class ExampleSub(Example):
        b: str
        c: float = attribute()

    ex = ExampleSub("pi", 3.14)

    assert ex.b == "pi"
    assert ex.c == 3.14
    assert not hasattr(ex, "a")
