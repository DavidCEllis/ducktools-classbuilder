# Ducktools: Class Builder #

`ducktools-classbuilder` is *the* Python package that will bring you the **joy**
of writing... **functions that write object protocols**...

Maybe that's just me.

This module provides a toolkit for building class generators, for creating
your own implementation of the same concept as `dataclasses` or `attrs`.

`ducktools.classbuilder` contains the tools for building a class generator
and `ducktools.classbuilder.prefab` includes a prebuilt implementation
from this base.

## Slot Class Usage ##

The building toolkit does include a basic implementation that uses
`__slots__` to define the fields by assigning a `SlotFields` instance.

```python
from ducktools.classbuilder import slotclass, Field, SlotFields

@slotclass
class SlottedDC:
    __slots__ = SlotFields(
        the_answer=42,
        the_question=Field(
            default="What do you get if you multiply six by nine?",
            doc="Life, the Universe, and Everything",
        ),
    )
    
ex = SlottedDC()
print(ex)
```

## Why does the basic implementation use slots? ##

Dataclasses has a problem when you use `@dataclass(slots=True)`, 
although this is not unique to dataclasses but inherent to the way both
`__slots__` and decorators work.

In order for this to *appear* to work, dataclasses has to make a new class 
and attempt to copy over everything from the original. This is because 
decorators operate on classes *after they have been created* while slots 
need to be declared beforehand. While you can change the value of `__slots__` 
after a class has been created, this will have no effect on the internal
structure of the class.

By declaring the class using `__slots__` on the other hand, we can take
advantage of the fact that it accepts a mapping, where the keys will be
used as the attributes to create as slots. The values can then be used as
the default values equivalently to how type hints are used in dataclasses.

For example these two classes would be roughly equivalent, except 
dataclasses has had to recreate the class from scratch while slotclasses
has simply added the methods on to the original class. This is easy to 
demonstrate using another decorator.

> This example requires Python 3.10 as earlier versions of 
> `dataclasses` did not support the `slots` argument.

```python
from dataclasses import dataclass
from ducktools.classbuilder import slotclass, SlotFields

class_register = {}


def register(cls):
    class_register[cls.__name__] = cls
    return cls


@dataclass(slots=True)
@register
class DataCoords:
    x: float = 0.0
    y: float = 0.0


@slotclass
@register
class SlotCoords:
    __slots__ = SlotFields(x=0.0, y=0.0)
    # Type hints don't affect class construction, these are optional.
    x: float
    y: float


print(DataCoords())
print(SlotCoords())

print(f"{DataCoords is class_register[DataCoords.__name__] = }")
print(f"{SlotCoords is class_register[SlotCoords.__name__] = }")

```

## What features does this have? ##

Included as an example implementation, the `slotclass` generator supports 
`default_factory` for creating mutable defaults like lists, dicts etc.
It also supports default values that are not builtins (try this on 
[Cluegen](https://github.com/dabeaz/cluegen)).

It will copy values provided as the `type` to `Field` into the 
`__annotations__` dictionary of the class. 
Values provided to `doc` will be placed in the final `__slots__` 
field so they are present on the class if `help(...)` is called.

If you want something with more features you can look at the `prefab.py`
implementation which provides a 'prebuilt' implementation.

## Customising and extending? ##

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

There are some examples of customising and extending the code generator in 
the documentation.

## How about... ##

I think that's enough examples.

You're encouraged to look at 
[the source](https://github.com/DavidCEllis/ducktools-classbuilder/blob/main/src/ducktools/classbuilder/__init__.py)
and build on it yourself at this point.

## Credit ##

Heavily inspired by [David Beazley's Cluegen](https://github.com/dabeaz/cluegen)
