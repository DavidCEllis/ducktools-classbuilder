## Examples of extending builders ##

Here are some examples of adding specific features to classes using the tools provided
by the `ducktools.classbuilder` module.

### How can I add `<method>` to the class ###

To do this you need to write a code generator that returns source code
along with a 'globals' dictionary of any names the code needs to refer 
to, or an empty dictionary if none are needed. Many methods don't require
any globals values, but it is essential for some.

#### Frozen Classes ####

In order to make frozen classes you need to replace `__setattr__` and `__delattr__`

The building blocks for this are actually already included as they're used to prevent 
`Field` subclass instances from being mutated when under testing.

These methods can be reused to make `slotclasses` 'frozen'.

```python
from ducktools.classbuilder import (
   slotclass,
   SlotFields,
   default_methods,
   frozen_setattr_maker,
   frozen_delattr_maker,
)

new_methods = default_methods | {frozen_setattr_maker, frozen_delattr_maker}


def frozen(cls, /):
   return slotclass(cls, methods=new_methods)


if __name__ == "__main__":
   @frozen
   class FrozenEx:
      __slots__ = SlotFields(
         x=6,
         y=9,
         product=42,
      )


   ex = FrozenEx()
   print(ex)

   try:
      ex.y = 7
   except TypeError as e:
      print(e)

   try:
      ex.z = "new value"
   except TypeError as e:
      print(e)

   try:
      del ex.y
   except TypeError as e:
      print(e)
```

#### Iterable Classes ####

Say you want to make the class iterable, so you want to add `__iter__`.

```python
from ducktools.classbuilder import (
    default_methods,
    get_fields,
    slotclass,
    GeneratedCode,
    MethodMaker,
    SlotFields,
)


def iter_generator(cls, funcname="__iter__"):
    field_names = get_fields(cls).keys()
    field_yield = "\n".join(f"    yield self.{f}" for f in field_names)
    if not field_yield:
        field_yield = "    yield from ()"
    code = f"def {funcname}(self):\n{field_yield}"
    globs = {}
    return GeneratedCode(code, globs)


iter_maker = MethodMaker("__iter__", iter_generator)
new_methods = frozenset(default_methods | {iter_maker})


def iterclass(cls=None, /):
    return slotclass(cls, methods=new_methods)


if __name__ == "__main__":
    @iterclass
    class IterDemo:
        __slots__ = SlotFields(
            a=1,
            b=2,
            c=3,
            d=4,
            e=5,
        )

    ex = IterDemo()
    print([item for item in ex])
```

You could also choose to yield tuples of `name, value` pairs in your implementation.

### Extending Field ###

The `Field` class can also be extended as if it is a slotclass, with annotations or
with `Field` declarations.

One notable caveat - if you want to use a `default_factory` in extending `Field` you
need to declare `default=FIELD_NOTHING` also in order for default to be ignored. This
is a special case for `Field` and is not needed in general.

```python
from ducktools.classbuilder import Field, FIELD_NOTHING

class MetadataField(Field):
    metadata: dict = Field(default=FIELD_NOTHING, default_factory=dict)
```

In regular classes the `__init__` function generator considers `NOTHING` to be an 
ignored value, but for `Field` subclasses it is a valid value so `FIELD_NOTHING` is
the ignored term. This is all because `None` *is* a valid value and can't be used
as a sentinel for Fields (otherwise `Field(default=None)` couldn't work).

#### Positional Only Arguments? ####

This is possible, but a little longer as we also need to modify multiple methods
along with adding a check to the builder to catch likely errors before the `__init__`
method is generated.

For simplicity this demonstration version will ignore the existence of the kw_only
parameter for fields.

```python
from ducktools.classbuilder import (
    builder,
    eq_maker,
    get_fields,
    slot_gatherer,
    Field,
    GeneratedCode,
    SlotFields,
    NOTHING,
    MethodMaker,
)


class PosOnlyField(Field):
    __slots__ = SlotFields(pos_only=True)


def init_generator(cls, funcname="__init__"):
    fields = get_fields(cls)

    arglist = []
    assignments = []
    globs = {}

    used_posonly = False
    used_kw = False

    for k, v in fields.items():
        if getattr(v, "pos_only", False):
            used_posonly = True
        elif used_posonly and not used_kw:
            used_kw = True
            arglist.append("/")

        if v.default is not NOTHING:
            globs[f"_{k}_default"] = v.default
            arg = f"{k}=_{k}_default"
            assignment = f"self.{k} = {k}"
        elif v.default_factory is not NOTHING:
            globs[f"_{k}_factory"] = v.default_factory
            arg = f"{k}=None"
            assignment = f"self.{k} = _{k}_factory() if {k} is None else {k}"
        else:
            arg = f"{k}"
            assignment = f"self.{k} = {k}"

        arglist.append(arg)
        assignments.append(assignment)

    args = ", ".join(arglist)
    assigns = "\n    ".join(assignments)
    code = f"def {funcname}(self, {args}):\n" f"    {assigns}\n"
    return GeneratedCode(code, globs)


def repr_generator(cls, funcname="__repr__"):
    fields = get_fields(cls)
    content_list = []
    for name, field in fields.items():
        if getattr(field, "pos_only", False):
            assign = f"{{self.{name}!r}}"
        else:
            assign = f"{name}={{self.{name}!r}}"
        content_list.append(assign)

    content = ", ".join(content_list)
    code = (
        f"def {funcname}(self):\n"
        f"    return f'{{type(self).__qualname__}}({content})'\n"
    )
    globs = {}
    return GeneratedCode(code, globs)


init_maker = MethodMaker("__init__", init_generator)
repr_maker = MethodMaker("__repr__", repr_generator)
new_methods = frozenset({init_maker, repr_maker, eq_maker})


def pos_slotclass(cls, /):
    cls = builder(
        cls,
        gatherer=slot_gatherer,
        methods=new_methods,
    )

    # Check no positional-only args after keyword args
    flds = get_fields(cls)
    used_kwarg = False
    for k, v in flds.items():
        if getattr(v, "pos_only", False):
            if used_kwarg:
                raise SyntaxError(
                    f"Positional only parameter {k!r}"
                    f" follows keyword parameters on {cls.__name__!r}"
                )
        else:
            used_kwarg = True

    return cls


if __name__ == "__main__":
    @pos_slotclass
    class WorkingEx:
        __slots__ = SlotFields(
            a=PosOnlyField(default=42),
            x=6,
            y=9,
        )

    ex = WorkingEx()
    print(ex)
    ex = WorkingEx(42, x=6, y=9)
    print(ex)

    try:
        ex = WorkingEx(a=54)
    except TypeError as e:
        print(e)

    try:
        @pos_slotclass
        class FailEx:
            __slots__ = SlotFields(
                a=42,
                x=PosOnlyField(default=6),
                y=PosOnlyField(default=9),
            )
    except SyntaxError as e:
        print(e)
```

#### Frozen Attributes ####

Here's an implementation that allows freezing of individual attributes.

```python
import ducktools.classbuilder as dtbuild


class FreezableField(dtbuild.Field):
    frozen: bool = False


def setattr_generator(cls, funcname="__setattr__"):
    globs = {}

    flags = dtbuild.get_flags(cls)
    fields = dtbuild.get_fields(cls)

    frozen_fields = set(
        name for name, field in fields.items()
        if getattr(field, "frozen", False)
    )

    globs["__frozen_fields"] = frozen_fields

    if flags.get("slotted", True):
        globs["__setattr_func"] = object.__setattr__
        setattr_method = "__setattr_func(self, name, value)"
        attrib_check = "hasattr(self, name)"
    else:
        setattr_method = "self.__dict__[name] = value"
        attrib_check = "name in self.__dict__"

    code = (
        f"def {funcname}(self, name, value):\n"
        f"    if name in __frozen_fields and {attrib_check}:\n"
        f"        raise AttributeError(\n"
        f"            f'Attribute {{name!r}} does not support assignment'\n"
        f"        )\n"
        f"    else:\n"
        f"        {setattr_method}\n"
    )

    return dtbuild.GeneratedCode(code, globs)


def delattr_generator(cls, funcname="__delattr__"):
    globs = {}

    flags = dtbuild.get_flags(cls)
    fields = dtbuild.get_fields(cls)

    frozen_fields = set(
        name for name, field in fields.items()
        if getattr(field, "frozen", False)
    )

    globs["__frozen_fields"] = frozen_fields

    if flags.get("slotted", True):
        globs["__delattr_func"] = object.__delattr__
        delattr_method = "__delattr_func(self, name)"
    else:
        delattr_method = "del self.__dict__[name]"

    code = (
        f"def {funcname}(self, name):\n"
        f"    if name in __frozen_fields:"
        f"        raise AttributeError(\n"
        f"            f'Attribute {{name!r}} is frozen and can not be deleted'\n"
        f"        )\n"
        f"    else:\n"
        f"        {delattr_method}\n"
    )

    return dtbuild.GeneratedCode(code, globs)


frozen_setattr_field_maker = dtbuild.MethodMaker("__setattr__", setattr_generator)
frozen_delattr_field_maker = dtbuild.MethodMaker("__delattr__", delattr_generator)
gatherer = dtbuild.make_unified_gatherer(FreezableField)


def freezable(cls=None, /, *, frozen=False):
    if cls is None:
        return lambda cls_: freezable(cls_, frozen=frozen)

    # To make a slotted class use a base class with metaclass
    flags = {"frozen": frozen, "slotted": False}

    cls = dtbuild.builder(
        cls,
        gatherer=gatherer,
        methods=dtbuild.default_methods,
        flags=flags,
    )

    # Frozen attributes need to be added afterwards
    # Due to the need to know if frozen fields exist
    if frozen:
        setattr(cls, "__setattr__", dtbuild.frozen_setattr_maker)
        setattr(cls, "__delattr__", dtbuild.frozen_delattr_maker)
    else:
        fields = dtbuild.get_fields(cls)
        has_frozen_fields = False
        for f in fields.values():
            if getattr(f, "frozen", False):
                has_frozen_fields = True
                break

        if has_frozen_fields:
            setattr(cls, "__setattr__", frozen_setattr_field_maker)
            setattr(cls, "__delattr__", frozen_delattr_field_maker)

    return cls


@freezable
class X:
    a: int = 2
    b: int = FreezableField(default=12, frozen=True)


x = X()
x.a = 21

try:
    x.b = 43
except AttributeError as e:
    print(repr(e))
```

#### Converters ####

Here's an implementation of basic converters that always convert when
their attribute is set.

```python
from ducktools.classbuilder import (
    builder,
    default_methods,
    get_fields,
    slot_gatherer,
    Field,
    GeneratedCode,
    SlotFields,
    MethodMaker,
)


class ConverterField(Field):
    converter = Field(default=None)


def setattr_generator(cls, funcname="__setattr__"):
    fields = get_fields(cls)
    converters = {}
    for k, v in fields.items():
        if conv := getattr(v, "converter", None):
            converters[k] = conv

    globs = {
        "_converters": converters,
        "_object_setattr": object.__setattr__,
    }

    code = (
        f"def {funcname}(self, name, value):\n"
        f"    if conv := _converters.get(name):\n"
        f"        _object_setattr(self, name, conv(value))\n"
        f"    else:\n"
        f"        _object_setattr(self, name, value)\n"
    )

    return GeneratedCode(code, globs)


setattr_maker = MethodMaker("__setattr__", setattr_generator)
methods = frozenset(default_methods | {setattr_maker})


def converterclass(cls, /):
    return builder(cls, gatherer=slot_gatherer, methods=methods)


if __name__ == "__main__":
    @converterclass
    class ConverterEx:
        __slots__ = SlotFields(
            unconverted=ConverterField(),
            converted=ConverterField(converter=int),
        )

    ex = ConverterEx("42", "42")
    print(ex)

```

### Gatherers ###
#### What about using annotations instead of `Field(init=False, ...)` ####

This seems to be a feature people keep requesting for `dataclasses`.

To implement this you need to create a new annotated_gatherer function.

> Note: Field classes will be frozen when running under pytest.
>       They should not be mutated by gatherers.
>       If you need to change the value of a field use Field.from_field(...) to make a new instance.

```python
# Don't use __future__ annotations with get_ns_annotations in this case 
# as it doesn't evaluate string annotations.

import types
from typing import Annotated, Any, ClassVar, get_origin

from ducktools.classbuilder import (
    builder,
    default_methods,
    get_fields,
    get_methods,
    slot_gatherer,
    Field,
    SlotMakerMeta,
    NOTHING,
)

from ducktools.classbuilder.annotations import get_ns_annotations


# Our 'Annotated' tools need to be combinable and need to contain the keyword argument
# and value they are intended to change.
# To this end we make a FieldModifier class that stores the keyword values given in a
# dictionary as 'modifiers'. This makes it easy to merge modifiers later.
class FieldModifier:
    __slots__ = ("modifiers",)
    modifiers: dict[str, Any]

    def __init__(self, **modifiers):
        self.modifiers = modifiers

    def __repr__(self):
        mod_args = ", ".join(f"{k}={v!r}" for k, v in self.modifiers.items())
        return (
            f"{type(self).__name__}({mod_args})"
        )

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return self.modifiers == other.modifiers
        return NotImplemented


# Here we make the modifiers and give them the arguments to Field we
# wish to change with their usage.
KW_ONLY = FieldModifier(kw_only=True)
NO_INIT = FieldModifier(init=False)
NO_REPR = FieldModifier(repr=False)
NO_COMPARE = FieldModifier(compare=False)
IGNORE_ALL = FieldModifier(init=False, repr=False, compare=False)


# Analyse the class and create these new Fields based on the annotations
def annotated_gatherer(cls_or_ns):
    if isinstance(cls_or_ns, (types.MappingProxyType, dict)):
        cls_dict = cls_or_ns
    else:
        cls_dict = cls_or_ns.__dict__

    cls_annotations = get_ns_annotations(cls_dict)
    cls_fields = {}

    # This gatherer doesn't make any class modifications but still needs
    # To have a dict as a return value
    cls_modifications = {}

    for key, anno in cls_annotations.items():
        modifiers = {}

        if get_origin(anno) is Annotated:
            meta = anno.__metadata__
            for v in meta:
                if isinstance(v, FieldModifier):
                    # Merge the modifier arguments to pass to AnnoField
                    modifiers.update(v.modifiers)

            # Extract the actual annotation from the first argument
            anno = anno.__origin__

        if anno is ClassVar or get_origin(anno) is ClassVar:
            continue

        if key in cls_dict:
            val = cls_dict[key]
            if isinstance(val, Field):
                # Make a new field - DO NOT MODIFY FIELDS IN PLACE
                fld = Field.from_field(val, type=anno, **modifiers)
                cls_modifications[key] = NOTHING
            elif not isinstance(val, types.MemberDescriptorType):
                fld = Field(default=val, type=anno, **modifiers)
                cls_modifications[key] = NOTHING
            else:
                fld = Field(type=anno, **modifiers)
        else:
            fld = Field(type=anno, **modifiers)

        cls_fields[key] = fld

    return cls_fields, cls_modifications


# As a decorator
def annotatedclass(cls=None, *, kw_only=False):
    if not cls:
        return lambda cls_: annotatedclass(cls_, kw_only=kw_only)

    return builder(
        cls,
        gatherer=annotated_gatherer,
        methods=default_methods,
        flags={"slotted": False, "kw_only": kw_only}
    )


# As a base class with slots
class AnnotatedClass(metaclass=SlotMakerMeta):
    # This attribute tells the slotmaker to use this gatherer
    _meta_gatherer = annotated_gatherer

    def __init_subclass__(cls, kw_only=False, **kwargs):
        slots = "__slots__" in cls.__dict__

        # if slots is True then fields will already be present in __slots__
        # Use the slot_gatherer for this case
        gatherer = slot_gatherer if slots else annotated_gatherer

        builder(
            cls,
            gatherer=gatherer,
            methods=default_methods,
            flags={"slotted": slots, "kw_only": kw_only}
        )

        super().__init_subclass__(**kwargs)


if __name__ == "__main__":
    from pprint import pp

    # Make classes, one via decorator one via subclass
    @annotatedclass
    class X:
        x: str
        y: ClassVar[str] = "This should be ignored"
        z: Annotated[ClassVar[str], "Should be ignored"] = "This should also be ignored"
        a: Annotated[int, NO_INIT] = "Not In __init__ signature"
        b: Annotated[str, NO_REPR] = "Not In Repr"
        c: Annotated[list[str], NO_COMPARE] = Field(default_factory=list)
        d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
        e: Annotated[str, KW_ONLY, NO_COMPARE]


    class Y(AnnotatedClass):
        x: str
        y: ClassVar[str] = "This should be ignored"
        z: Annotated[ClassVar[str], "Should be ignored"] = "This should also be ignored"
        a: Annotated[int, NO_INIT] = "Not In __init__ signature"
        b: Annotated[str, NO_REPR] = "Not In Repr"
        c: Annotated[list[str], NO_COMPARE] = Field(default_factory=list)
        d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
        e: Annotated[str, KW_ONLY, NO_COMPARE]


    # Unslotted Demo
    ex = X("Value of x", e="Value of e")
    print(ex, "\n")

    pp(get_fields(X))
    print("\n")

    # Slotted Demo
    ex = Y("Value of x", e="Value of e")
    print(ex, "\n")

    print(f"Slots: {Y.__dict__.get('__slots__')}")

    print("\nSource:")

    # Obtain the methods set on the class X
    methods = get_methods(X)

    # Call the code generators to display the source code
    for method in methods.values():
        # Both classes generate identical source code
        genX = method.code_generator(X)
        genY = method.code_generator(Y)
        assert genX == genY

        print(genX.source_code)
```
