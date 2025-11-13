# Prefab - A prebuilt classbuilder implementation  #

This is a more full featured dataclass replacement with some different design decisions
and features.

Including:
* Declaration by type hints, slots or `attribute(...)` assignment on the class
* `__prefab_pre_init__` and `__prefab_post_init__` detection to allow for validation/conversion
* Optional `as_dict` method generation to convert to a dictionary
* Optional recursive `__repr__` handling (off by default)

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

Or with type hints:

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

Pre-slotted classes can be created by using the `Prefab` base class

```python
from ducktools.classbuilder.prefab import Prefab


class Settings(Prefab):
    hostname: str = "localhost"
    template_folder: str = 'base/path'
    template_name: str = 'index'
```

## Why not just use attrs or dataclasses? ##

If attrs or dataclasses solves your problem then you should use them.
They are thoroughly tested, well supported packages. This is a new
project and has not had the rigorous real world testing of either
of those.

This module has been created for situations where startup time is important,
such as for CLI tools and for handling conversion of inputs in a way that
was more useful to me than attrs converters (`__prefab_post_init__`).

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
    * `prefab` uses a `get_attributes` function to return the attributes as a dict.
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
    * use the `Prefab` base class if you wish your classes to be automatically slotted.
    * `@prefab` can be used if the slots are provided with a `__slots__ = SlotFields(...)`
      attribute set.
    * The support for slots in `attrs` and `dataclasses` involves recreating the
      class as it is not possible to effectively define `__slots__` after class
      creation. This can cause bugs where decorators or caches hold references
      to the original class.
1. InitVar annotations are not supported.
    * So far I haven't needed this yet so it hasn't been implemented.
1. The `__repr__` method for prefabs will have a different output if it will not `eval` correctly.
    * This isn't a guarantee that the regular `__repr__` will eval, but if it is known
      that the output would not `eval` then an alternative repr is used which does not
      look like it would `eval`.
1. default_factory functions will be called if `None` is passed as an argument
    * This makes it easier to wrap the function.
1. The `Prefab` base class will automatically create the `__dict__` slot if
   `cached_property` is used in the class.
   * This means that cached properties will work as expected in slotted classes
     but that you will also be able to set any attribute in non-frozen classes