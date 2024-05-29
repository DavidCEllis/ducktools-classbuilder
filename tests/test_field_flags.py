from ducktools.classbuilder import Field, SlotFields, slotclass
import inspect


def test_init_false_field():
    @slotclass
    class Example:
        __slots__ = SlotFields(
            x=Field(default="x", init=False),
            y=Field(default="y")
        )

    sig = inspect.signature(Example)
    assert 'x' not in sig.parameters
    assert 'y' in sig.parameters
    assert sig.parameters["y"].default == "y"

    ex = Example()
    assert ex.x == "x"
    assert ex.y == "y"


def test_repr_false_field():
    @slotclass
    class Example:
        __slots__ = SlotFields(
            x=Field(default="x", repr=False),
            y=Field(default="y"),
        )

    ex = Example()
    assert repr(ex).endswith("Example(y='y')")


def test_compare_false_field():
    @slotclass
    class Example:
        __slots__ = SlotFields(
            x=Field(default="x", compare=False),
            y=Field(default="y"),
        )

    ex = Example()
    ex2 = Example(x="z")
    ex3 = Example(y="z")

    assert ex == ex2
    assert ex != ex3
