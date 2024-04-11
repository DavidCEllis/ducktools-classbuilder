# Prefab - A prebuilt classbuilder implementation  #

```{toctree}
---
maxdepth: 2
caption: "Contents:"
hidden: true
---
index
pre_post_init
dataclasses_differences
api
```

Writes the class boilerplate code so you don't have to.

Unlike `slotclass` in classbuilder this is a more featureful implementation.

Including:
* Declaration by type hints, slots or `attribute(...)` assignment on the class
* `attribute` arguments to include/exclude fields from specific methods or to make them keyword only
* `prefab` arguments to modify class generation options
* `__prefab_pre_init__` and `__prefab_post_init__` detection to allow for validation/conversion
* Frozen classes
* Optional `as_dict` method generation
* Optional recursive `__repr__` handling

## Usage ##

Define the class using plain assignment and `attribute` function calls:

```python
from ducktools.classbuilder.prefab import prefab, attribute

@prefab
class Settings:
    hostname = attribute(default="localhost")
    template_folder = attribute(default='base/path')
    template_name = attribute(default='index')
```

Or with type hinting:

```python
from ducktools.classbuilder.prefab import prefab

@prefab
class Settings:
    hostname: str = "localhost"
    template_folder: str = 'base/path'
    template_name: str = 'index'
```

In either case the result behaves the same.

```python
>>> s = Settings()
>>> print(s)
Settings(hostname='localhost', template_folder='base/path', template_name='index')
```

For further details see the `usage` pages in the documentation.

## Slots ##

Classes can also be created using `__slots__` in the same way as `@slotclass` from the builder,
but with all of the additional features added by `prefab`

Similarly to the type hinted form, plain values given to a SlotFields instance are treated as defaults
while `attribute` calls are handled normally. `doc` values will be seen when calling `help(...)` on the class
while the `__annotations__` dictionary will be updated with `type` values given. Annotations can also still
be given normally (which will probably be necessary for static typing tools).

```python
from ducktools.classbuilder.prefab import prefab, attribute, SlotFields

@prefab
class Settings:
    __slots__ = SlotFields(
        hostname="localhost",
        template_folder="base/path",
        template_name=attribute(default="index", type=str, doc="Name of the template"),
    )
```

## Why not just use attrs or dataclasses? ##

If attrs or dataclasses solves your problem then you should use them.
They are thoroughly tested, well supported packages. This is a new
project and has not had the rigorous real world testing of either
of those.

This module has been created for situations where startup time is important, 
such as for CLI tools and for handling conversion of inputs in a way that
was more useful to me than attrs converters (`__prefab_post_init__`).

## How does it work ##

The `@prefab` decorator analyses the class it is decorating and prepares an internals dict, along
with performing some other early checks.
Once this is done it sets any direct values (`PREFAB_FIELDS` and `__match_args__` if required) 
and places non-data descriptors for all of the magic methods to be generated.

The non-data descriptors for each of the magic methods perform code generation when first called
in order to generate the actual methods. Once the method has been generated, the descriptor is 
replaced on the class with the resulting method so there is no overhead regenerating the method
on each access. 

By only generating methods the first time they are used the start time can be
improved and methods that are never used don't have to be created at all (for example the 
`__repr__` method is useful when debugging but may not be used in normal runtime). In contrast
`dataclasses` generates all of its methods when the class is created.
