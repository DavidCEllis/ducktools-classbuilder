# Building your own class generator #

The core idea is that there are 3 main parts to the generation process:

1. Gather the fields from the decorated class.
2. Gather inherited fields from any parent classes in the standard 
   method resolution order.
3. Assign the method builders to the class.

The field gathering is done by a function that operates on the class and returns
a dictionary of field_name: field values. `slot_gatherer` is an example of this.
This function is provided to `builder` as the `gatherer` argument.

The inheritance is handled by the `builder` function itself and should not need
to be customisable.

Assignment of method builders is where all of the functions that will lazily
create `__init__` and other magic methods are added to the class.

This might be easier to understand by looking at examples so here are a few
demonstrations of adding additional features to the builder.

### How can I add `<method>` to the class ###

To do this you need to write a code generator that returns source code
along with a dictionary of any variables the code needs to refer to, or
an empty dictionary if none are needed.

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

### What if I want to exclude fields from a method? ###

In order to exclude fields you first need to extend the `Field` class
to add a new attribute. Thankfully the `@fieldclass` decorator can be used
to extend `Field` in the same way as `@slotclass` works for regular classes.

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

### How about Frozen Classes? ###

Here's an example of frozen slotted classes that only allow assignment once
(which happens in the `__init__` method generated).

```python
from ducktools.classbuilder import (
    slotclass,
    get_fields,
    SlotFields,
    MethodMaker,
    default_methods,
)


def setattr_maker(cls):
    globs = {
        "object_setattr": object.__setattr__
    }

    field_names = set(get_fields(cls).keys())

    code = (
        f"def __setattr__(self, name, value):\n"
        f"    fields = {field_names!r}\n"
        f"    if name in fields and not hasattr(self, name):\n"
        f"        object_setattr(self, name, value)\n"
        f"    else:\n"
        f'        raise TypeError("{cls.__name__!r} object does not support attribute assignment")'
    )
    return code, globs


def delattr_maker(cls):
    code = (
        f"def __delattr__(self, name):\n"
        f'    raise TypeError("{cls.__name__!r} object does not support attribute deletion")'
    )
    globs = {}
    return code, globs


setattr_desc = MethodMaker("__setattr__", setattr_maker)
delattr_desc = MethodMaker("__delattr__", delattr_maker)

new_methods = frozenset(default_methods | {setattr_desc, delattr_desc})


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

### What if I want to use type hints instead of slots? ###

Really? Have you heard of [dataclasses](https://docs.python.org/3/library/dataclasses.html)?

But we can also do that. These classes will not be slotted, however, 
due to the issues mentioned earlier.

```python
import sys
from ducktools.classbuilder import builder, default_methods, Field, NOTHING


def _is_classvar(hint):
    # Avoid importing typing if it's not already used
    _typing = sys.modules.get("typing")
    if _typing:
        if (
            hint is _typing.ClassVar
            or getattr(hint, "__origin__", None) is _typing.ClassVar
        ):
            return True
        # String used as annotation
        elif isinstance(hint, str) and "ClassVar" in hint:
            return True
    return False


def annotation_gatherer(cls):
    cls_annotations = cls.__dict__.get("__annotations__", {})
    cls_fields = {}

    for k, v in cls_annotations.items():
        # Ignore ClassVar
        if _is_classvar(v):
            continue

        attrib = getattr(cls, k, NOTHING)

        if attrib is not NOTHING:
            if isinstance(attrib, Field):
                attrib.type = v
            else:
                attrib = Field(default=attrib)

            # Remove the class variable
            delattr(cls, k)

        else:
            attrib = Field()

        cls_fields[k] = attrib

    return cls_fields


def annotation_class(cls=None, /, *, methods=default_methods):
    return builder(cls, gatherer=annotation_gatherer, methods=methods)


if __name__ == "__main__":
    import typing

    @annotation_class
    class H2G2:
        the_answer: int = 42
        the_question: str = Field(
            default="What do you get if you multiply six by nine?",
        )
        the_book: typing.ClassVar[str] = "The Hitchhiker's Guide to the Galaxy"
        the_author: "typing.ClassVar[str]" = "Douglas Adams"

    ex = H2G2()
    print(ex)
    ex2 = H2G2(
        the_question="What is the ultimate answer to the meaning of life, the universe, and everything?"
    )
    print(ex2)

    print(H2G2.the_book)
    print(H2G2.the_author)
```

### Positional Only Arguments? ###

Also possible, but a little longer as we need to modify multiple methods
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

### What if I wanted converters ###

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