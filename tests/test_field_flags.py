from ducktools.classbuilder import Field, SlotFields, slotclass
import inspect

from utils import graalpy_fails  # type: ignore


@graalpy_fails
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


@graalpy_fails
def test_repr_false_field():
    @slotclass
    class Example:
        __slots__ = SlotFields(
            x=Field(default="x", repr=False),
            y=Field(default="y"),
        )

    ex = Example()
    assert repr(ex).endswith("Example(y='y')")


@graalpy_fails
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


@graalpy_fails
def test_kwonly_true_field():
    @slotclass
    class Example:
        __slots__ = SlotFields(
            a="a",
            b=Field(default="b", kw_only=True),
            c="c"
        )

    # Check the signature is correct
    params = inspect.signature(Example).parameters

    assert params["a"].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert params["b"].kind == inspect.Parameter.KEYWORD_ONLY
    assert params["c"].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    assert params["a"].default == "a"
    assert params["b"].default == "b"
    assert params["c"].default == "c"

    # Check the values are set correctly inside __init__
    ex = Example(a="a", b="b", c="c")
    assert (ex.a, ex.b, ex.c) == ("a", "b", "c")

    ex2 = Example("A", "C")
    assert (ex2.a, ex2.b, ex2.c) == ("A", "b", "C")

    ex3 = Example(b="B")
    assert (ex3.a, ex3.b, ex3.c) == ("a", "B", "c")

    @slotclass
    class ExampleNoDefaults:
        __slots__ = SlotFields(
            a=Field(),
            b=Field(kw_only=True),
            c=Field(),
        )

    params = inspect.signature(ExampleNoDefaults).parameters

    assert params["a"].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert params["b"].kind == inspect.Parameter.KEYWORD_ONLY
    assert params["c"].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    assert params["a"].default is inspect.Parameter.empty
    assert params["b"].default is inspect.Parameter.empty
    assert params["c"].default is inspect.Parameter.empty

    ex = ExampleNoDefaults("a", "c", b="b")

    assert (ex.a, ex.b, ex.c) == ("a", "b", "c")
