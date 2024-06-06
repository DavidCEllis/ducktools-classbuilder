# Prefab - A prebuilt classbuilder implementation  #

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

## Pre and Post Init Methods ##

Alongside the standard method generation `@prefab` decorated classes
have special behaviour if `__prefab_pre_init__` or `__prefab_post_init__`
methods are defined.

For both methods if they have additional arguments with names that match
defined attributes, the matching arguments to `__init__` will be passed
through to the method. 

**If an argument is passed to `__prefab_post_init__`it will not be initialized
in `__init__`**. It is expected that initialization will occur in the method
defined by the user.

Other than this, arguments provided to pre/post init do not modify the behaviour
of their corresponding attributes (they will still appear in the other magic
methods).

Examples have had repr and eq removed for brevity.

### Examples ###

#### \_\_prefab_pre_init\_\_ ####

Input code:

```python
from ducktools.classbuilder.prefab import prefab

@prefab(repr=False, eq=False)
class ExampleValidate:
    x: int
    
    @staticmethod
    def __prefab_pre_init__(x):
        if x <= 0:
            raise ValueError("x must be a positive integer")
```

Equivalent code:

```python
class ExampleValidate:
    PREFAB_FIELDS = ['x']
    __match_args__ = ('x',)
    
    def __init__(self, x: int):
        self.__prefab_pre_init__(x=x)
        self.x = x
    
    @staticmethod
    def __prefab_pre_init__(x):
        if x <= 0:
            raise ValueError('x must be a positive integer')
```

#### \_\_prefab_post_init\_\_ ####

Input code:

```python
from ducktools.classbuilder.prefab import prefab, attribute
from pathlib import Path

@prefab(repr=False, eq=False)
class ExampleConvert:
    x: Path = attribute(default='path/to/source')

    def __prefab_post_init__(self, x: Path | str):
        self.x = Path(x)
```

Equivalent code:

```python
from pathlib import Path
class ExampleConvert:
    PREFAB_FIELDS = ['x']
    __match_args__ = ('x',)
    
    x: Path
    
    def __init__(self, x: Path | str = 'path/to/source'):
        self.__prefab_post_init__(x=x)
    
    def __prefab_post_init__(self, x: Path | str):
        self.x = Path(x)
```

## Differences with dataclasses ##

While this project doesn't intend to exactly replicate other similar
modules it's worth noting where they differ in case users get tripped up.

Prefabs don't behave quite the same (externally) as dataclasses. They are
very different internally.

This doesn't include things that haven't been implemented, and only focuses
on intentional differences. Unintentional differences may be patched
or will be added to this list.

### Functional differences ###
1. prefabs do not generate the comparison methods other than `__eq__`.
    * This isn't generally a feature I want or use, however with the tools it is easy
      to add if this is a needed feature.
1. the `as_dict` method in `prefab_classes` does *not* behave the same as 
   dataclasses' `asdict`.
    * `as_dict` does *not* deepcopy the included fields, modification of mutable
      fields in the dictionary will modify them in the original object.
    * `as_dict` does *not* recurse
      - Recursion would require knowing how other objects should be serialized.
      - dataclasses `asdict`'s recursion appears to be for handling json serialization
        prefab expects the json serializer to handle recursion.
1. dataclasses provides a `fields` function to access the underlying fields.
    * Prefab classes provide a `PREFAB_FIELDS` attribute with the field names
      in order for quick access.
    * There is also a `get_attributes` function that will return the attributes.
1. Plain `attribute(...)` declarations can be used without the use of type hints.
    * If a plain assignment is used, all assignments **must** use `attribute`.
1. Post init processing uses `__prefab_post_init__` instead of `__post_init__`
    * This is just a case of not wanting any confusion between the two.
    * `attrs` similarly does `__attrs_post_init__`.
    * `__prefab_pre_init__` can also be used to define something to run
      before the body of `__init__`.
    * If an attribute name is provided as an argument to either the pre_init
      or post_init functions the value will be passed through.
1. Unlike dataclasses, prefab classes will let you use unhashable default
   values.
    * This isn't to say that mutable defaults are a good idea in general but
      prefabs are supposed to behave like regular classes and regular classes
      let you make this mistake.
    * Usually you should use `attribute(default_factory=list)` or similar.
1. If `init` is `False` in `@prefab(init=False)` the method is still generated
   but renamed to `__prefab_init__`.
1. Slots are supported but not from annotations using the decorator `@prefab`
    * The support for slots in `attrs` and `dataclasses` involves recreating the
      class as it is not possible to effectively define `__slots__` after class 
      creation. This can cause bugs where decorators or caches hold references
      to the original class.
    * `@prefab` can be used if the slots are provided with a `__slots__ = SlotFields(...)`
      attribute set.
    * Alternately, classes created via the `Prefab` base class are automatically slotted
      unless `slots=False` is used.
1. InitVar annotations are not supported.
    * Passing arguments to `__prefab_post_init__` is done by adding the argument
      to the method signature.
    * Assignment is automatically skipped for any such values, default factories
      will be called and passed to the post init method.
1. The `__repr__` method for prefabs will have a different output if it will not `eval` correctly.
    * This isn't a guarantee that the regular `__repr__` will eval, but if it is known
      that the output would not `eval` then an alternative repr is used which does not
      look like it would `eval`.
1. default_factory functions will be called if `None` is passed as an argument
    * This makes it easier to wrap the function.


## API Autodocs ##

### Core Functions ###

```{eval-rst}
.. autofunction:: ducktools.classbuilder.prefab::prefab
```

```{eval-rst}
.. autofunction:: ducktools.classbuilder.prefab::attribute
```

```{eval-rst}
.. autofunction:: ducktools.classbuilder.prefab::build_prefab
```

### Helper functions ###

```{eval-rst}
.. autofunction:: ducktools.classbuilder.prefab::is_prefab
.. autofunction:: ducktools.classbuilder.prefab::is_prefab_instance
.. autofunction:: ducktools.classbuilder.prefab::as_dict
```
