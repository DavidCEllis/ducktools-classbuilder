# Ducktools: Class Builder #

`ducktools-classbuilder` is *the* Python package that will bring you the **joy**
of writing... functions... that will bring back the **joy** of writing classes.

Maybe.

While `attrs` and `dataclasses` are class boilerplate generators, 
`ducktools.classbuilder` is intended to provide the tools to help make a customized
version of the same concept.

Install from PyPI with:
`python -m pip install ducktools-classbuilder`

## Included Implementations ##

There are 2 different implementations provided with the module each of which offers
a subclass based and decorator based option.

> [!TIP]
> For more information on using these tools to create your own implementations 
> using the builder see
> [the tutorial](https://ducktools-classbuilder.readthedocs.io/en/latest/tutorial.html)
> for a full tutorial and 
> [extension_examples](https://ducktools-classbuilder.readthedocs.io/en/latest/extension_examples.html)
> for other customizations.

### Core ###

These tools are available from the main `ducktools.classbuilder` module.

* `@slotclass`
  * A decorator based implementation that uses a special dict subclass assigned
     to `__slots__` to describe the fields for method generation.
* `SlotMakerMeta`
  * A metaclass for creating other implementations using annotations, fields or slots.
  * This metaclass will allow for creating `__slots__` correctly in subclasses.
* `builder`
  * This is the main tool used for constructing decorators and base classes to provide
    generated methods.

Each of these forms of class generation will result in the same methods being 
attached to the class after the field information has been obtained.

```python
from ducktools.classbuilder import Field, SlotFields, slotclass

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

### Prefab ###

This is available from the `ducktools.classbuilder.prefab` submodule.

This includes more customization including `__prefab_pre_init__` and `__prefab_post_init__`
functions for subclass customization.

A `@prefab` decorator and `Prefab` base class are provided. 

`Prefab` will generate `__slots__` by default.
decorated classes with `@prefab` that do not declare fields using `__slots__`
will **not** be slotted and there is no `slots` argument to apply this.

Here is an example of applying a conversion in `__post_init__`:
```python
from pathlib import Path
from ducktools.classbuilder.prefab import Prefab

class AppDetails(Prefab, frozen=True):
    app_name: str
    app_path: Path

    def __prefab_post_init__(self, app_path: str | Path):
        # frozen in `Prefab` is implemented as a 'set-once' __setattr__ function.
        # So we do not need to use `object.__setattr__` here
        self.app_path = Path(app_path)

steam = AppDetails(
    "Steam",
    r"C:\Program Files (x86)\Steam\steam.exe"
)

print(steam)
```


## What is the issue with generating `__slots__` with a decorator ##

If you want to use `__slots__` in order to save memory you have to declare
them when the class is originally created as you can't add them later.

When you use `@dataclass(slots=True)`[^2] with `dataclasses`, the function 
has to make a new class and attempt to copy over everything from the original.

This is because decorators operate on classes *after they have been created* 
while slots need to be declared beforehand. 
While you can change the value of `__slots__` after a class has been created, 
this will have no effect on the internal structure of the class.

By using a metaclass or by declaring fields using `__slots__` however,
the fields can be set *before* the class is constructed, so the class
will work correctly without needing to be rebuilt.

For example these two classes would be roughly equivalent, except that
`@dataclass` has had to recreate the class from scratch while `Prefab`
has created `__slots__` and added the methods on to the original class. 
This means that any references stored to the original class *before*
`@dataclass` has rebuilt the class will not be pointing towards the 
correct class.

Here's a demonstration of the issue using a registry for serialization 
functions.

> This example requires Python 3.10 or later as earlier versions of 
> `dataclasses` did not support the `slots` argument.

```python
import json
from dataclasses import dataclass
from ducktools.classbuilder.prefab import Prefab, attribute


class _RegisterDescriptor:
    def __init__(self, func, registry):
        self.func = func
        self.registry = registry

    def __set_name__(self, owner, name):
        self.registry.register(owner, self.func)
        setattr(owner, name, self.func)


class SerializeRegister:
    def __init__(self):
        self.serializers = {}

    def register(self, cls, func):
        self.serializers[cls] = func

    def register_method(self, method):
        return _RegisterDescriptor(method, self)

    def default(self, o):
        try:
            return self.serializers[type(o)](o)
        except KeyError:
            raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


register = SerializeRegister()


@dataclass(slots=True)
class DataCoords:
    x: float = 0.0
    y: float = 0.0

    @register.register_method
    def to_json(self):
        return {"x": self.x, "y": self.y}


# slots=True is the default for Prefab
class BuilderCoords(Prefab):
    x: float = 0.0
    y: float = attribute(default=0.0, doc="y coordinate")

    @register.register_method
    def to_json(self):
        return {"x": self.x, "y": self.y}


# In both cases __slots__ have been defined
print(f"{DataCoords.__slots__ = }")
print(f"{BuilderCoords.__slots__ = }\n")

data_ex = DataCoords()
builder_ex = BuilderCoords()

objs = [data_ex, builder_ex]

print(data_ex)
print(builder_ex)
print()

# Demonstrate you can not set values not defined in slots
for obj in objs:
    try:
        obj.z = 1.0
    except AttributeError as e:
        print(e)
print()

print("Attempt to serialize:")
for obj in objs:
    try:
        print(f"{type(obj).__name__}: {json.dumps(obj, default=register.default)}")
    except TypeError as e:
        print(f"{type(obj).__name__}: {e!r}")
```

Output (Python 3.12):
```
DataCoords.__slots__ = ('x', 'y')
BuilderCoords.__slots__ = {'x': None, 'y': 'y coordinate'}

DataCoords(x=0.0, y=0.0)
BuilderCoords(x=0.0, y=0.0)

'DataCoords' object has no attribute 'z'
'BuilderCoords' object has no attribute 'z'

Attempt to serialize:
DataCoords: TypeError('Object of type DataCoords is not JSON serializable')
BuilderCoords: {"x": 0.0, "y": 0.0}
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

If you want something with more features you can look at the `prefab`
submodule which provides more specific features that differ further from the 
behaviour of `dataclasses`.

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