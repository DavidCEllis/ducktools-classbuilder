# Tests for the core 'builder'
import inspect
import pytest

from ducktools.classbuilder import (
    INTERNALS_DICT,
    NOTHING,
    get_fields,
    get_flags,
    MethodMaker,
    init_maker,
    builder,
    Field,
    SlotFields,
    slot_gatherer,
    slotclass,
    GatheredFields,
)
from ducktools.classbuilder.annotations import get_annotations


def test_get_fields_flags():
    local_fields = {"Example": Field()}
    resolved_fields = {"ParentField": Field(), "Example": Field()}
    flags = {"slotted": False}

    internals_dict = {
        "fields": resolved_fields,
        "local_fields": local_fields,
        "flags": flags,
    }

    class ExampleFields:
        ...

    setattr(ExampleFields, INTERNALS_DICT, internals_dict)

    assert get_fields(ExampleFields) == resolved_fields
    assert get_fields(ExampleFields, local=True) == local_fields
    assert get_flags(ExampleFields) == flags


def test_method_maker():
    def generator(cls):
        code = "def demo(self): return self.x"
        globs = {}
        return code, globs

    method_desc = MethodMaker("demo", generator)

    assert repr(method_desc) == "<MethodMaker for 'demo' method>"

    class ValueX:
        demo = method_desc

        def __init__(self):
            self.x = "Example Value"

    ex = ValueX()

    assert ValueX.__dict__["demo"] == method_desc

    assert ex.x == "Example Value"
    assert ex.demo() == "Example Value"

    # Should no longer be equal as demo was called
    assert ValueX.__dict__["demo"] != method_desc


def test_construct_field():
    f = Field()
    assert f.default is NOTHING
    assert f.default_factory is NOTHING
    assert f.type is NOTHING
    assert f.doc is None

    with pytest.raises(AttributeError):
        Field(default=None, default_factory=list)


def test_eq_field():
    f1 = Field(default=True)
    f2 = Field(default=False)
    f3 = Field(default_factory=list)
    f4 = Field(default=True, type=bool)
    f5 = Field(default=True, doc="True or False")

    assert f1 != f2
    assert f1 != f3
    assert f1 != f4
    assert f1 != f5

    f1r = Field(default=True)
    assert f1 == f1r


def test_from_field():
    f1 = Field(default=True)
    f2 = Field(default=False)
    f3 = Field(default_factory=list)
    f4 = Field(default=True, type=bool)
    f5 = Field(default=True, doc="True or False")

    for fld in [f1, f2, f3, f4, f5]:
        assert fld == Field.from_field(fld)
        assert fld is not Field.from_field(fld)


def test_repr_field():
    f1 = Field(default=True)
    f2 = Field(default=False)
    f3 = Field(default_factory=list)
    f4 = Field(default=True, type=bool)
    f5 = Field(default=True, doc="True or False")

    nothing_repr = repr(NOTHING)

    f1_repr = f"Field(default=True, default_factory={nothing_repr}, type={nothing_repr}, doc=None)"
    f2_repr = f"Field(default=False, default_factory={nothing_repr}, type={nothing_repr}, doc=None)"
    f3_repr = f"Field(default={nothing_repr}, default_factory=<class 'list'>, type={nothing_repr}, doc=None)"
    f4_repr = f"Field(default=True, default_factory={nothing_repr}, type=<class 'bool'>, doc=None)"
    f5_repr = f"Field(default=True, default_factory={nothing_repr}, type={nothing_repr}, doc='True or False')"

    assert repr(f1) == f1_repr
    assert repr(f2) == f2_repr
    assert repr(f3) == f3_repr
    assert repr(f4) == f4_repr
    assert repr(f5) == f5_repr


def test_frozen_field():
    # UNDER TESTING FIELD SHOULD BE FROZEN
    f = Field(default=True)

    attr_changes = {
        "default": False,
        "default_factory": list,
        "type": bool,
        "doc": "This should fail",
    }

    for k, v in attr_changes.items():
        with pytest.raises(TypeError):
            setattr(f, k, v)

    for k in attr_changes:
        with pytest.raises(TypeError):
            delattr(f, k)


def test_slot_gatherer_success():

    fields = {
        "a": Field(default=1),
        "b": Field(default=2),
        "c": Field(default_factory=list, doc="a list"),
        "d": Field(type=str)
    }

    class SlotsExample:
        a: int

        __slots__ = SlotFields(
            a=1,
            b=Field(default=2),
            c=Field(default_factory=list, doc="a list"),
            d=Field(type=str),
        )

    slots, modifications = slot_gatherer(SlotsExample)

    assert slots == fields
    assert modifications["__slots__"] == {"a": None, "b": None, "c": "a list", "d": None}
    assert modifications["__annotations__"] == {"a": int, "d": str}
    assert get_annotations(SlotsExample.__dict__) == {"a": int}  # Original annotations dict unmodified


def test_slot_gatherer_failure():
    class NoSlots:
        ...

    with pytest.raises(AttributeError):
        slot_gatherer(NoSlots)

    class WrongSlots:
        __slots__ = ["a", "b", "c"]

    with pytest.raises(TypeError):
        slot_gatherer(WrongSlots)

    class DictSlots:
        __slots__ = {"a": "documentation"}

    with pytest.raises(TypeError):
        slot_gatherer(DictSlots)


def test_slotclass_empty():
    @slotclass
    class SlotClass:
        __slots__ = SlotFields()

    ex = SlotClass()
    ex2 = SlotClass()

    assert repr(ex) == "test_slotclass_empty.<locals>.SlotClass()"
    assert ex == ex2


def test_slotclass_methods():

    class SlotClass:
        __slots__ = SlotFields()

    assert "__init__" not in SlotClass.__dict__
    assert "__repr__" not in SlotClass.__dict__
    assert "__eq__" not in SlotClass.__dict__

    SlotClass = slotclass(SlotClass)

    assert "__init__" in SlotClass.__dict__
    assert "__repr__" in SlotClass.__dict__
    assert "__eq__" in SlotClass.__dict__


def test_slotclass_attributes():
    @slotclass
    class SlotClass:
        __slots__ = SlotFields(
            a=1,
            b=Field(default=2, type=int),
            c=Field(default_factory=list, doc="a list"),
        )

    prefix = "test_slotclass_attributes.<locals>."

    ex = SlotClass()
    ex2 = SlotClass()
    ex3 = SlotClass(c=[1, 2, 3])
    ex4 = SlotClass(4, 5, [1, 2, 3])

    assert ex.a == 1
    assert ex.b == 2
    assert ex.c == []

    assert ex3.c == [1, 2, 3]

    assert ex4.a == 4
    assert ex4.b == 5
    assert ex4.c == [1, 2, 3]

    assert ex == ex2
    assert ex != ex3

    assert repr(ex) == f"{prefix}SlotClass(a=1, b=2, c=[])"
    assert repr(ex3) == f"{prefix}SlotClass(a=1, b=2, c=[1, 2, 3])"


def test_slotclass_nodefault():
    @slotclass
    class SlotClass:
        __slots__ = SlotFields(
            a=Field(),
            b=2,
            c=Field(default_factory=list, doc="a list"),
        )

    ex = SlotClass(1)
    ex2 = SlotClass(a=2, b=4, c=[8, 16, 32])

    assert ex.a == 1
    assert ex.b == 2
    assert ex.c == []

    assert ex2.a == 2
    assert ex2.b == 4
    assert ex2.c == [8, 16, 32]


def test_slotclass_ordering():
    with pytest.raises(SyntaxError):
        # Non-default argument after default
        @slotclass
        class OrderingError:
            __slots__ = SlotFields(
                x=1,
                y=Field(),
            )


def test_slotclass_norepr_noeq():
    @slotclass(methods={init_maker})
    class SlotClass:
        __slots__ = SlotFields(
            a=Field(),
            b=2,
            c=Field(default_factory=list, doc="a list"),
        )

    assert "__repr__" not in SlotClass.__dict__
    assert "__eq__" not in SlotClass.__dict__


def test_slotclass_weakref():
    import weakref

    @slotclass
    class WeakrefClass:
        __slots__ = SlotFields(
            a=1,
            b=2,
            __weakref__=None,
        )

    flds = get_fields(WeakrefClass)
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


def test_slotclass_dict():
    @slotclass
    class DictClass:
        __slots__ = SlotFields(
            a=1,
            b=2,
            __dict__=None,
        )

    flds = get_fields(DictClass)
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


def test_fieldclass():
    class NewField(Field):
        __slots__ = SlotFields(serialize=True)
        serialize: bool

    f = NewField()

    assert f.default is NOTHING
    assert f.default_factory is NOTHING
    assert f.type is NOTHING
    assert f.doc is None
    assert f.serialize is True

    f2 = NewField(default=1, serialize=False)

    assert f2.default == 1
    assert f2.serialize is False

    with pytest.raises(TypeError):
        # All arguments are keyword only in fieldclasses
        NewField(42)


def test_fieldclass_frozen():
    class NewField(Field, frozen=True):
        __slots__ = SlotFields(serialize=True)
        serialize: bool

    f = NewField()

    attr_changes = {
        "default": False,
        "default_factory": list,
        "type": bool,
        "doc": "This should fail",
        "serialize": False,
    }

    for k, v in attr_changes.items():
        with pytest.raises(TypeError):
            setattr(f, k, v)

    for k in attr_changes:
        with pytest.raises(TypeError):
            delattr(f, k)

    # Even slotted fields raise TypeError as setattr happens first
    with pytest.raises(TypeError):
        setattr(f, "new_attribute", False)

    with pytest.raises(TypeError):
        delattr(f, "new_attribute")


def test_builder_noclass():
    mini_slotclass = builder(gatherer=slot_gatherer, methods={init_maker})

    @mini_slotclass
    class SlotClass:
        __slots__ = SlotFields(
            a=Field(),
            b=2,
            c=Field(default_factory=list, doc="a list"),
        )

    assert "__init__" in SlotClass.__dict__
    assert "__repr__" not in SlotClass.__dict__
    assert "__eq__" not in SlotClass.__dict__

    x = SlotClass(12)
    assert x.a == 12
    assert x.b == 2
    assert x.c == []


def test_gatheredfields():
    fields = {"x": Field(default=1)}
    modifications = {"x": NOTHING}

    alt_fields = {"x": Field(default=1), "y": Field(default=2)}

    flds = GatheredFields(fields, modifications)
    flds_2 = GatheredFields(fields, modifications)
    flds_3 = GatheredFields(alt_fields, modifications)

    class Ex:
        pass

    assert flds(Ex) == (fields, modifications)

    assert flds == flds_2
    assert flds != flds_3
    assert flds != object()

    assert repr(flds).endswith(
        "GatheredFields("
        "fields={'x': Field(default=1, default_factory=<NOTHING OBJECT>, type=<NOTHING OBJECT>, doc=None)}, "
        "modifications={'x': <NOTHING OBJECT>}"
        ")"
    )

def test_signature():
    # This used to fail
    @slotclass
    class SigClass:
        __slots__ = SlotFields(x=42)

    assert str(inspect.signature(SigClass)) == "(x=42)"
