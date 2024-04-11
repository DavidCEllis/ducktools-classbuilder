# Ducktools: Class Builder #

`ducktools-classbuilder` is *the* Python package that will bring you the **joy**
of writing... functions... that will bring back the **joy** of writing classes.

Maybe.

While `attrs` and `dataclasses` are class boilerplate generators, 
`ducktools.classbuilder` is intended to be a dataclasses-like generator.
The goal is to handle some of the basic functions and to allow for flexible
customization of both the field collection and the method generation.

`ducktools.classbuilder.prefab` includes a prebuilt implementation using these tools.

## Slot Class Usage ##

The building toolkit also includes a basic implementation that uses
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
`@dataclass` has had to recreate the class from scratch while `@slotclass`
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

For more information on creating class generators using the builder
see [the docs](https://ducktools-classbuilder.readthedocs.io/en/latest/extension_examples.html)

## Will you add \<feature\> to `classbuilder.prefab`? ##

No. Not unless it's something I need or find interesting.

The original version of `prefab_classes` was intended to have every feature
anybody could possibly require, but this is no longer the case with this
rebuilt version.

I will fix bugs (assuming they're not actually intended behaviour).

However the whole goal of this module is if you want to have a class generator
with a specific feature, you can create or add it yourself.

## Credit ##

Heavily inspired by [David Beazley's Cluegen](https://github.com/dabeaz/cluegen)
