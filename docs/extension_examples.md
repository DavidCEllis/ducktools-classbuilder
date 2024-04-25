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

## Structure ##

### The Builder Function ###

```{eval-rst}
.. autofunction:: ducktools.classbuilder::builder
  :noindex:
```

This function is the core class generator which takes your decorated class and
analyses and collects valid fields and then attaches the method makers.

The field information is stored in the `INTERNALS_DICT` attribute which should generally
not need to be accessed directly. `get_fields` and `get_flags` functions are to be
used to access the important keys.

`get_fields(cls)` will return the resolved information obtained from this class and subclasses.

`get_fields(cls, local=True)` will return the field information obtained from **this class only**.

Now let's look at what the keyword arguments to `builder` need to be.

#### Flags ####

Flags are information that defines how the entire class should be generated, for use by
method generators when operating on the class.

The default makers in `ducktools.classbuilder` make use of one flag - `"kw_only"` - 
which indicates that a class `__init__` function should only take keyword arguments.

Prefabs also make use of a `"slotted"` flag to indicate if the class has been generated
with `__slots__` (checking for the existence of `__slots__` could find that a user has
manually placed slots in the class).

Flags are set using a dictionary with these keys and boolean values, for example:

`cls = builder(cls, gatherer=..., methods=..., flags={"kw_only": True, "slotted": True})` 

#### Gatherers ####

This covers the *'gather the fields'* step of the process.

A `gatherer` in this case is a function which takes in the class and returns a dict
of `{"field_name": Field(...)}` values based on some analysis of your class.

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
          doc="I always knew there was something fundamentally wrong with the universe."
       )
    )

pprint(slot_gatherer(GatherExample))
```

#### Methods ####

`methods` needs to be a set of `MethodMaker` instances which are descriptors that
replace themselves with the required methods on first access.

A `MethodMaker` takes two arguments:
`funcname` - the name of the method to attach
`code_generator` - a code generator function that returns a tuple of source code and globals dict.

```{eval-rst}
.. autoclass:: ducktools.classbuilder::MethodMaker
  :noindex:
```

An example of these descriptors is the `init_desc` method maker that generates the `__init__`
function. Their behaviour is best observed by looking at the class after it is generated.

```python
from ducktools.classbuilder import slotclass, SlotFields, Field, init_desc

@slotclass
class GatherExample:
    __slots__ = SlotFields(
       x=6,
       y=9,
       z=Field(
          default=42,
          doc="I always knew there was something fundamentally wrong with the universe."
       )
    )

# Access through the __dict__ to avoid code generation
print(f'Before generation: {GatherExample.__dict__["__init__"] = }')

# Now generate the code by forcing python to call __init__
ex = GatherExample()

print(f'After generation: {GatherExample.__dict__["__init__"] = }')

# Look at the contents of the maker
print("\nDescriptor Contents: ")
print(f"{init_desc.funcname = }")
print(f"{init_desc.code_generator = }\n")

# Look at the output of the code generator
generated = init_desc.code_generator(GatherExample)
print(f"Globals: {generated[1]!r}")
print(f"Source:\n{generated[0]}")
```

### Extending `Field` ###

When customising generator methods (or adding new ones) it may be useful to 
extend the `Field` class which stores the information on named attributes for
how to perform the generation. A convenient decorator `@fieldclass` is provided
to allow simple extension by adding additional slots. By using this decorator
the `__init__`, `__repr__` and `__eq__` methods will be generated for you.

> Note: Field classes will be frozen when running under pytest.
>       They are not frozen normally for performance reasons.

```python
from ducktools.classbuilder import Field, SlotFields, fieldclass

@fieldclass
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
`fieldclass` instances from being mutated.

These methods can be reused to make `slotclasses` 'frozen'.

```python
from ducktools.classbuilder import (
    slotclass,
    SlotFields,
    default_methods,
    frozen_setattr_desc,
    frozen_delattr_desc,
)


new_methods = default_methods | {frozen_setattr_desc, frozen_delattr_desc}


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
    default_methods, get_fields, slotclass, MethodMaker, SlotFields
)


def iter_maker(cls):
    field_names = get_fields(cls).keys()
    field_yield = "\n".join(f"    yield self.{f}" for f in field_names)
    code = (
        f"def __iter__(self):\n"
        f"{field_yield}"
    )
    globs = {}
    return code, globs


iter_desc = MethodMaker("__iter__", iter_maker)
new_methods = frozenset(default_methods | {iter_desc})


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

#### Excluding Attributes ####

In order to exclude fields you first need to extend the `Field` class
to add a new attribute. Thankfully the `@fieldclass` decorator mentioned earlier
can be used to extend `Field` in the same way as `@slotclass` works for 
regular classes.

This special class builder is needed to treat `NOTHING` sentinel values as
regular values in the `__init__` generator. As such this is only intended
for use on `Field` subclasses.

You also need to rewrite the code generator to check for the new attribute 
and exclude the field if it is `False`.

Here is an example of adding the ability to exclude fields from `__repr__`.

```python
from ducktools.classbuilder import (
    eq_desc,
    fieldclass,
    get_fields,
    init_desc,
    slotclass,
    Field,
    SlotFields,
    MethodMaker,
)


@fieldclass
class FieldExt(Field):
    __slots__ = SlotFields(repr=True)


def repr_exclude_maker(cls):
    fields = get_fields(cls)

    # Use getattr with default True for the condition so
    # regular fields without the 'repr' field still work
    content = ", ".join(
        f"{name}={{self.{name}!r}}"
        for name, field in fields.items()
        if getattr(field, "repr", True)
    )
    code = (
        f"def __repr__(self):\n"
        f"    return f'{{type(self).__qualname__}}({content})'\n"
    )
    globs = {}
    return code, globs


repr_desc = MethodMaker("__repr__", repr_exclude_maker)


if __name__ == "__main__":

    methods = frozenset({init_desc, eq_desc, repr_desc})

    @slotclass(methods=methods)
    class Example:
        __slots__ = SlotFields(
            the_answer=42,
            the_question=Field(
                default="What do you get if you multiply six by nine?",
                doc="Life, the Universe, and Everything",
            ),
            the_book=FieldExt(
                default="The Hitchhiker's Guide to the Galaxy",
                repr=False,
            )
        )

    ex = Example()
    print(ex)
    print(ex.the_book)
```

#### Positional Only Arguments? ####

Also possible, but a little longer as we also need to modify multiple methods
along with adding a check to the builder.

The additional check in the builder is needed to prevent more confusing
errors when the `__init__` method is generated.

```python
from ducktools.classbuilder import (
    builder,
    eq_desc,
    fieldclass,
    get_fields,
    slot_gatherer,
    Field,
    SlotFields,
    NOTHING,
    MethodMaker,
)


@fieldclass
class PosOnlyField(Field):
    __slots__ = SlotFields(pos_only=True)


def init_maker(cls):
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
    return code, globs


def repr_maker(cls):
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
    return code, globs


init_desc = MethodMaker("__init__", init_maker)
repr_desc = MethodMaker("__repr__", repr_maker)
new_methods = frozenset({init_desc, repr_desc, eq_desc})


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
    fieldclass,
    get_fields,
    slot_gatherer,
    Field,
    SlotFields,
    MethodMaker,
)


@fieldclass
class ConverterField(Field):
    __slots__ = SlotFields(converter=None)


def setattr_maker(cls):
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

    return code, globs


setattr_desc = MethodMaker("__setattr__", setattr_maker)
methods = frozenset(default_methods | {setattr_desc})


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
This is also doable.

> Note: Field classes will be frozen when running under pytest.
>       They should not be mutated by gatherers.
>       If you need to change the value of a field use Field.from_field(...) to make a new instance.

```python
import inspect
from pprint import pp
from typing import Annotated, Any, ClassVar, get_origin

from ducktools.classbuilder import (
    builder,
    fieldclass,
    get_fields,
    get_flags,
    Field,
    MethodMaker,
    SlotFields,
    NOTHING,
)


# New equivalent to dataclasses "Field", these still need to be created
# in order to generate the magic methods correctly.
@fieldclass
class AnnoField(Field):
    __slots__ = SlotFields(
        init=True,
        repr=True,
        compare=True,
        kw_only=False,
    )


# Modifying objects
class FieldModifier:
    __slots__ = ("modifiers", )
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


KW_ONLY = FieldModifier(kw_only=True)
NO_INIT = FieldModifier(init=False)
NO_REPR = FieldModifier(repr=False)
NO_COMPARE = FieldModifier(compare=False)
IGNORE_ALL = FieldModifier(init=False, repr=False, compare=False)


def annotated_gatherer(cls: type) -> dict[str, Any]:
    # String annotations *MUST* be evaluated for this to work
    # dataclasses currently does not require this
    cls_annotations = inspect.get_annotations(cls, eval_str=True)
    cls_fields = {}

    for key, anno in cls_annotations.items():
        modifiers = {}
        typ = NOTHING

        if get_origin(anno) is Annotated:
            typ = anno.__args__[0]
            meta = anno.__metadata__
            for v in meta:
                if isinstance(v, FieldModifier):
                    modifiers.update(v.modifiers)

        elif not (anno is ClassVar or get_origin(anno) is ClassVar):
            typ = anno

        if typ is not NOTHING:
            if key in cls.__dict__ and "__slots__" not in cls.__dict__:
                val = cls.__dict__[key]
                if isinstance(val, Field):
                    fld = AnnoField.from_field(val, type=typ, **modifiers)
                else:
                    fld = AnnoField(default=val, type=typ, **modifiers)
            else:
                fld = AnnoField(type=typ, **modifiers)

            cls_fields[key] = fld

    return cls_fields


def init_maker(cls):

    fields = get_fields(cls)
    flags = get_flags(cls)

    arglist = []
    kw_only_arglist = []

    assignments = []
    globs = {}

    # Whole class kw_only
    kw_only = flags.get("kw_only", False)

    for k, v in fields.items():
        if getattr(v, "init", True):
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

            if getattr(v, "kw_only", False) or kw_only:
                kw_only_arglist.append(arg)
            else:
                arglist.append(arg)

            assignments.append(assignment)
        else:
            if v.default is not NOTHING:
                globs[f"_{k}_default"] = v.default
                assignment = f"self.{k} = _{k}_default"
                assignments.append(assignment)
            elif v.default_factory is not NOTHING:
                globs[f"_{k}_factory"] = v.default_factory
                assignment = f"self.{k} = _{k}_factory()"
                assignments.append(assignment)

    if kw_only_arglist:
        arglist.append("*")
        arglist.extend(kw_only_arglist)

    args = ", ".join(arglist)
    assigns = "\n    ".join(assignments)
    code = f"def __init__(self, {args}):\n" f"    {assigns}\n"

    return code, globs


def repr_maker(cls):
    fields = get_fields(cls)
    content = ", ".join(
        f"{name}={{self.{name}!r}}"
        for name, fld in fields.items()
        if getattr(fld, "repr", True)
    )
    code = (
        f"def __repr__(self):\n"
        f"    return f'{{type(self).__qualname__}}({content})'\n"
    )
    globs = {}
    return code, globs


def eq_maker(cls):
    class_comparison = "self.__class__ is other.__class__"
    field_names = [
        name
        for name, fld in get_fields(cls).items()
        if getattr(fld, "compare", True)
    ]

    if field_names:
        selfvals = ",".join(f"self.{name}" for name in field_names)
        othervals = ",".join(f"other.{name}" for name in field_names)
        instance_comparison = f"({selfvals},) == ({othervals},)"
    else:
        instance_comparison = "True"

    code = (
        f"def __eq__(self, other):\n"
        f"    return {instance_comparison} if {class_comparison} else NotImplemented\n"
    )
    globs = {}

    return code, globs


init_method = MethodMaker("__init__", init_maker)
repr_method = MethodMaker("__repr__", repr_maker)
eq_method = MethodMaker("__eq__", eq_maker)

methods = {init_method, repr_method, eq_method}


def annotationsclass(cls=None, *, kw_only=False):
    if not cls:
        return lambda cls_: annotationsclass(cls_, kw_only=kw_only)

    return builder(
        cls,
        gatherer=annotated_gatherer,
        methods=methods,
        flags={"slotted": False, "kw_only": kw_only}
    )


@annotationsclass
class X:
    x: str
    y: ClassVar[str] = "This is okay"
    a: Annotated[int, NO_INIT] = "Not In __init__ signature"
    b: Annotated[str, NO_REPR] = "Not In Repr"
    c: Annotated[list[str], NO_COMPARE] = AnnoField(default_factory=list)
    d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
    e: Annotated[str, KW_ONLY, NO_COMPARE]


ex = X("Value of x", e="Value of e")

print(ex, "\n")

pp(get_fields(X))
print("\nSource:")
print(init_maker(X)[0])
print(eq_maker(X)[0])
print(repr_maker(X)[0])
```
