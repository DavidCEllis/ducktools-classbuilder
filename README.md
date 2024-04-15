# Ducktools: Class Builder #

`ducktools-classbuilder` is *the* Python package that will bring you the **joy**
of writing... functions... that will bring back the **joy** of writing classes.

Maybe.

While `attrs` and `dataclasses` are class boilerplate generators, 
`ducktools.classbuilder` is intended to be a `@dataclass`-like generator.
The goal is to handle some of the basic functions and to allow for flexible
customization of both the field collection and the method generation.

`ducktools.classbuilder.prefab` includes a prebuilt implementation using these tools.

Install from PyPI with:
`python -m pip install ducktools-classbuilder`

## Usage: building a class decorator ##

In order to create a class decorator using `ducktools.classbuilder` there are
a few things you need to prepare.

1. A field gathering function to analyse the class and collect valid `Field`s.
   * An example `slot_gatherer` is included.
2. Code generators that can make use of the gathered `Field`s to create magic method
   source code.
   * Example `init_maker`, `repr_maker` and `eq_maker` generators are included.
3. A function that calls the `builder` function to apply both of these steps.

A field gathering function needs to take the original class as an argument and 
return a dictionary of `{key: Field(...)}` pairs.

> [!NOTE]
> The `builder` will handle inheritance so do not collect fields from parent classes.

The code generators take the class as the only argument and return a tuple 
of method source code and globals to be provided to `exec(code, globs)` in order 
to generate the actual method. 

The provided `slot_gatherer` looks for `__slots__` being assigned a `SlotFields` 
class[^1] where keyword arguments define the names and values for the fields. 

Code generator functions need to be converted to descriptors before being used. 
This is done using the provided `MethodMaker` descriptor class. 
ex: `init_desc = MethodMaker("__init__", init_maker)`

These parts can then be used to make a basic class boilerplate generator by 
providing them to the `builder` function.

```python
from ducktools.classbuilder import (
    builder, 
    slot_gatherer, 
    init_maker, eq_maker, repr_maker,
    MethodMaker,
)

init_desc = MethodMaker("__init__", init_maker)
repr_desc = MethodMaker("__repr__", repr_maker)
eq_desc = MethodMaker("__eq__", eq_maker)

def slotclass(cls):
    return builder(cls, gatherer=slot_gatherer, methods={init_desc, repr_desc, eq_desc})
```

## Slot Class Usage ##

This created `slotclass` function can then be used as a decorator to generate classes in 
a similar manner to the `@dataclass` decorator from `dataclasses`. 

> [!NOTE] 
> `ducktools.classbuilder` includes a premade version of `slotclass` that can
> be used directly. (The included version has some extra features).

```python
from ducktools.classbuilder import Field, SlotFields

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

> [!TIP]
> For more information and examples of creating class generators with additional 
> features using the builder see 
> [the docs](https://ducktools-classbuilder.readthedocs.io/en/latest/extension_examples.html)

## Why does your example use `__slots__` instead of annotations? ##

If you want to use `__slots__` in order to save memory you have to declare
them when the class is originally created as you can't add them later.

When you use `@dataclass(slots=True)`[^2] with `dataclasses` in order for 
this to work, `dataclasses` has to make a new class and attempt to
copy over everything from the original. 
This is because decorators operate on classes *after they have been created* 
while slots need to be declared beforehand. 
While you can change the value of `__slots__` after a class has been created, 
this will have no effect on the internal structure of the class.

By declaring the class using `__slots__` on the other hand, we can take
advantage of the fact that it accepts a mapping, where the keys will be
used as the attributes to create as slots. The values can then be used as
the default values equivalently to how type hints are used in `dataclasses`.

For example these two classes would be roughly equivalent, except that
`@dataclass` has had to recreate the class from scratch while `@slotclass`
has added the methods on to the original class. 
This means that any references stored to the original class *before*
`@dataclass` has rebuilt the class will not be pointing towards the 
correct class. 
This can be demonstrated using a simple class register decorator.

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

[^1]: `SlotFields` is actually just a subclassed `dict` with no changes. `__slots__`
      works with dictionaries using the values of the keys, while fields are normally
      used for documentation.

[^2]: or `@attrs.define`.