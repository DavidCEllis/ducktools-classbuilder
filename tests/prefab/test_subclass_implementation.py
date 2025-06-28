import inspect

import pytest

from ducktools.classbuilder.prefab import Prefab, Attribute, SlotFields, get_attributes


from utils import graalpy_fails  # type: ignore


@graalpy_fails
class TestConstructionForms:
    """
    Test the 3 different ways of constructing prefabs
    """
    def test_attributes(self):
        class Ex(Prefab):
            a = Attribute()
            b = Attribute(default=1)

        # Slotted by default
        assert "__slots__" in vars(Ex)
        assert isinstance(Ex.__slots__, dict)

        ex = Ex(1, 2)
        assert ex.a == 1
        assert ex.b == 2

    def test_annotations(self):
        class Ex(Prefab):
            a: int
            b: int = 1

        assert "__slots__" in vars(Ex)
        assert isinstance(Ex.__slots__, dict)

        ex = Ex(1, 2)
        assert ex.a == 1
        assert ex.b == 2

    def test_slots(self):
        class Ex(Prefab):
            __slots__ = SlotFields(
                a=Attribute(),
                b=1
            )

        assert "__slots__" in vars(Ex)
        assert isinstance(Ex.__slots__, dict)

        ex = Ex(1, 2)
        assert ex.a == 1
        assert ex.b == 2


class TestClassArguments:
    """
    Testing the non-default arguments given to a subclass
    to make sure they are passed through
    """
    def test_slots(self):
        class Ex(Prefab, slots=True):
            a: int
            b: int = 1

        assert "__slots__" in vars(Ex)

        class Ex(Prefab, slots=False):
            a: int
            b: int = 1

        assert "__slots__" not in vars(Ex)

    def test_init(self):
        class Ex(Prefab, init=True):
            a: int
            b: int = 1

        ex1 = Ex(0)
        ex2 = Ex(0, 1)
        ex3 = Ex(a=0, b=1)

        assert ex1 == ex2 == ex3

        class ExNoInit(Prefab, init=False):
            a: int
            b: int = 1

        assert "__init__" not in vars(ExNoInit)
        assert "__prefab_init__" in vars(ExNoInit)

        ex1 = ExNoInit()
        ex1.__prefab_init__(0, 1)

        assert (ex1.a, ex1.b) == (0, 1)

    def test_repr(self):
        class Ex(Prefab, repr=True):
            a: int
            b: int = 1

        assert "__repr__" in vars(Ex)

        class ExNoRepr(Prefab, repr=False):
            a: int
            b: int = 1

        assert "__repr__" not in vars(ExNoRepr)

    def test_eq(self):
        class Ex(Prefab, eq=True):
            a: int
            b: int = 1

        assert "__eq__" in vars(Ex)

        class ExNoEq(Prefab, eq=False):
            a: int
            b: int = 1

        assert "__eq__" not in vars(ExNoEq)

    def test_iter(self):
        class ExIter(Prefab, iter=True):
            a: int
            b: int = 1

        assert "__iter__" in vars(ExIter)

        class ExNoIter(Prefab, iter=False):
            a: int
            b: int = 1

        assert "__iter__" not in vars(ExNoIter)

        a, b = ExIter(0)
        assert (a, b) == (0, 1)

    def test_match_args(self):
        class Ex(Prefab, match_args=True):
            a: int
            b: int = 1

        assert "__match_args__" in vars(Ex)
        assert Ex.__match_args__ == ("a", "b")

        class ExNoMatchArgs(Prefab, match_args=False):
            a: int
            b: int = 1

        assert "__match_args__" not in vars(ExNoMatchArgs)

    def test_kw_only(self):
        class Ex(Prefab, kw_only=False):
            a: int
            b: int = 1

        ex1 = Ex(0)
        ex2 = Ex(0, 1)
        ex3 = Ex(a=0, b=1)
        ex4 = Ex(0, b=1)

        assert ex1 == ex2 == ex3 == ex4

        sig = inspect.signature(Ex)
        params = sig.parameters

        assert params['a'].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert params['b'].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert params['b'].default == 1

        class ExKWOnly(Prefab, kw_only=True):
            a: int
            b: int = 1

        with pytest.raises(TypeError):
            ex = ExKWOnly(0)

        sig = inspect.signature(ExKWOnly)
        params = sig.parameters

        assert params['a'].kind == inspect.Parameter.KEYWORD_ONLY
        assert params['b'].kind == inspect.Parameter.KEYWORD_ONLY
        assert params['b'].default == 1


@graalpy_fails
def test_slots_weakref():
    import weakref

    class WeakrefClass(Prefab):
        a: int = 1
        b: int = 2
        __weakref__: dict  # type: ignore

    flds = get_attributes(WeakrefClass)
    assert 'a' in flds
    assert 'b' in flds
    assert '__weakref__' not in flds

    slots = WeakrefClass.__slots__
    assert 'a' in slots
    assert 'b' in slots
    assert '__weakref__' in slots

    # Test weakrefs can be created
    inst = WeakrefClass()
    ref = weakref.ref(inst)
    assert ref == inst.__weakref__


def test_has_dict():
    class DictClass(Prefab):
        a: int = 1
        b: int = 2
        __dict__: dict  # type: ignore

    flds = get_attributes(DictClass)
    assert 'a' in flds
    assert 'b' in flds
    assert '__dict__' not in flds

    slots = DictClass.__slots__
    assert 'a' in slots
    assert 'b' in slots
    assert '__dict__' in slots

    # Test if __dict__ is included new values can be added
    inst = DictClass()
    inst.c = 42
    assert inst.__dict__ == {"c": 42}
