# Building your own class generator #

The core idea is that there are 3 parts to the process of generating
the class boilerplate that need to be handled:

1. Gather the fields from the decorated class.
2. Gather inherited fields from any parent classes in the standard 
   method resolution order.
3. Assign the method builders to the class.

This tool handles the second step for you and tries to make it easy to apply
the first and third steps.

The field gathering is done by a function that operates on the class and returns
a dictionary of field_name: field values. `slot_gatherer` is an example of this.
This function is provided to `builder` as the `gatherer` argument.

The inheritance is handled by the `builder` function itself and should not need
to be customisable.

Assignment of method builders is where all of the functions that will lazily
create `__init__` and other magic methods are added to the class.

## Creating a generator ##

### Gatherers ###

This covers the *'gather the fields'* step of the process.

A `gatherer` in this case is a function which takes in the class and returns both a dict
of `{"field_name": Field(...)}` values based on some analysis of your class and a second
dictionary of attributes to modify on the main class.

An example gatherer is given in `slot_gatherer` which will take the keys and values
from a dict subclass `SlotFields` and use that to prepare the field information for
the attached methods to use.

```{eval-rst}
.. autofunction:: ducktools.classbuilder::slot_gatherer
  :noindex:
```

You can test and see what this class returns by simply calling it on an undecorated
class.

> Note: The `<NOTHING OBJECT>` values you see are a sentinel used to show no value was given
> This is used instead of `None` where `None` might be a valid default value or type.

```python
from pprint import pprint
from ducktools.classbuilder import slot_gatherer, SlotFields, Field

class GatherExample:
    __slots__ = SlotFields(
       x=6,
       y=9,
       z=Field(
          default=42,
          doc="I always knew there was something fundamentally wrong with the universe.",
          type=int,
       )
    )

pprint(slot_gatherer(GatherExample))
```

Output:
```
({'x': Field(default=6, default_factory=<NOTHING OBJECT>, type=<NOTHING OBJECT>, doc=None),
  'y': Field(default=9, default_factory=<NOTHING OBJECT>, type=<NOTHING OBJECT>, doc=None),
  'z': Field(default=42, default_factory=<NOTHING OBJECT>, type=<class 'int'>, doc='I always knew there was something fundamentally wrong with the universe.')},
 {'__annotations__': {'z': <class 'int'>},
  '__slots__': {'x': None,
                'y': None,
                'z': 'I always knew there was something fundamentally wrong '
                     'with the universe.'}})
```

The first dictionary shows the field names and the information that will be used by
the code generators attached to the class to create any required magic methods.

The second dictionary shows which values on the original class are going to be replaced.
Replacing the value of `__slots__` at this point wont change the actual internal slots
but will provide the strings given as additional documentation to `help(GatherExample)`.

Here's a similar example using the `annotations_gatherer`

```python
from pprint import pprint
from ducktools.classbuilder import Field
from ducktools.classbuilder import annotation_gatherer


class GatherExample:
    x: int
    y: list[str] = Field(default_factory=list)
    z: int = Field(default=42, doc="Unused in non slot classes.")


pprint(annotation_gatherer(GatherExample))
```

Output:
```
({'x': Field(default=<NOTHING OBJECT>, default_factory=<NOTHING OBJECT>, type=<class 'int'>, doc=None),
  'y': Field(default=<NOTHING OBJECT>, default_factory=<class 'list'>, type=list[str], doc=None),
  'z': Field(default=42, default_factory=<NOTHING OBJECT>, type=<class 'int'>, doc='Unused in non slot classes.')},
 {'y': <NOTHING OBJECT>, 'z': 42})
```

Here we can see that the type values have been filled in based on the annotations provided.
The value of 'z' on the class is being replaced by the default value and the value of 'y'
appears to be set to a `<NOTHING OBJECT>`. The use of `NOTHING` here is actually an indicator
to the builder to remove this attribute from the class.

> Gatherer functions **should not** modify the class directly.
> All class modification should occur in the `builder` function.

### Methods ###

`methods` needs to be a set of `MethodMaker` instances which are descriptors that
replace themselves with the required methods on first access.

A `MethodMaker` takes two arguments:
`funcname` - the name of the method to attach - such as `__init__` or `__repr__`
`code_generator` - a code generator function.

```{eval-rst}
.. autoclass:: ducktools.classbuilder::MethodMaker
  :noindex:
```

The `code_generator` function to be provided needs to take the prepared class as the only argument 
and return a tuple of source code and a globals dictionary in which to execute the code.
These can be examined by looking at the output of any of the `<method>_generator` functions.
For example the included `init_generator`.

```python
from ducktools.classbuilder import init_generator
from ducktools.classbuilder import AnnotationClass

class InitExample(AnnotationClass):
   a: str
   b: str = "b"
   obj: object = object()
   
output = init_generator(InitExample)
print(output[0])
print(output[1])
```

Output:
```
def __init__(self, a, b=_b_default, obj=_obj_default):
    self.a = a
    self.b = b
    self.obj = obj

{'_b_default': 'b', '_obj_default': <object object at ...>}
```

> Note: The values are replaced by `_name_default` for defaults in the parameters
> in order to make sure that the defaults are the exact objects provided at generation.

To convert these into the actual functions these generators are provided to a
`MethodMaker` descriptor class. The `funcname` provided must match the name of 
the function in the generated code and will also be the attribute to which the 
descriptor is attached. `init_maker = MethodMaker('__init__', init_generator)`
in this case.

The `MethodMaker` descriptors actions can be observed by looking at the class
dictionary before and after `__init__` is first called.

```python
from ducktools.classbuilder import AnnotationClass


class InitExample(AnnotationClass):
   a: str
   b: str = "b"


# Access through the __dict__ to avoid code generation
print(f'Before generation: {InitExample.__dict__["__init__"] = }')

# Now generate the code by forcing python to call __init__
ex = InitExample("a")

print(f'After generation: {InitExample.__dict__["__init__"] = }')
```

Output:
```
Before generation: InitExample.__dict__["__init__"] = <MethodMaker for '__init__' method>
After generation: InitExample.__dict__["__init__"] = <function InitExample.__init__ at 0x0000027D256D51C0>
```

### Flags ###

Flags are information that defines how the entire class should be generated, for use by
method generators when operating on the class.

The default makers in `ducktools.classbuilder` make use of one flag - `"kw_only"` - 
which indicates that a class `__init__` function should only take keyword arguments.

Prefabs also make use of a `"slotted"` flag to indicate if the class has been generated
with `__slots__` (checking for the existence of `__slots__` could find that a user has
manually placed slots in the class).

Flags are set using a dictionary with these keys and boolean values, for example:

`cls = builder(cls, gatherer=..., methods=..., flags={"kw_only": True, "slotted": True})` 

### The Builder Function ###

```{eval-rst}
.. autofunction:: ducktools.classbuilder::builder
  :noindex:
```

Once all these pieces are in place they can be provided to the `builder` function.

This uses the provided `gatherer` to get the field information and attribute changes
that need to be made to the class.

When applying the attribute changes, any attribute values which are given as `NOTHING` are 
deleted. 
Afterwards it looks through parent classes and gathers a full set of inherited fields.

An internals dictionary is generated which contains the full inherited fields as `fields`,
the fields from the decorated class only as `local_fields` and any flags passed through
as `flags`. This is then stored in a `__classbuilder_internals__` attribute. These can be
accessed using the `get_fields` and `get_flags` functions provided.

`get_fields(cls)` will return the resolved information obtained from this class and subclasses.

`get_fields(cls, local=True)` will return the field information obtained from **this class only**.

### Extending `Field` ###

When customising generator methods (or adding new ones) it may be useful to 
extend the `Field` class which stores the information on named attributes for
how to perform the generation. This can be done by simply subclassing `Field`
and adding new attributes either via annotations or by assigning `SlotFields`
to `__slots__`.

> Note: Field classes will be frozen when running under pytest.
>       They are not frozen normally for performance reasons.

```python
from ducktools.classbuilder import Field, SlotFields

class WithInit(Field):
    __slots__ = SlotFields(init=True)

ex1 = WithInit(default=6, init=False)
ex2 = WithInit(default=9, init=True)
ex3 = WithInit(default=9)

print(ex1)
print(f"{ex1 == ex2 = }")
print(f"{ex2 == ex3 = }")
```

## Examples ##

This might be easier to understand by looking at examples so here are a few
demonstrations of adding additional features to the builder.

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


def iter_generator(cls):
    field_names = get_fields(cls).keys()
    field_yield = "\n".join(f"    yield self.{f}" for f in field_names)
    code = f"def __iter__(self):\n" f"{field_yield}"
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


def init_generator(cls):
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
    code = f"def __init__(self, {args}):\n" f"    {assigns}\n"
    return GeneratedCode(code, globs)


def repr_generator(cls):
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
        f"def __repr__(self):\n"
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


def setattr_generator(cls):
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
        f"def __setattr__(self, name, value):\n"
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

To implement this you simply need to create a new annotated_gatherer function.

> Note: Field classes will be frozen when running under pytest.
>       They should not be mutated by gatherers.
>       If you need to change the value of a field use Field.from_field(...) to make a new instance.

```python
from __future__ import annotations

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
