# classbuilder.prefab - Python Class Boilerplate Generator  #

Writes the class boilerplate code so you don't have to. 

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

Prefab Classes has been created for situations where startup time is important, 
such as for CLI tools and for handling conversion of inputs in a way that
was more useful to me than attrs converters (`__prefab_post_init__`).


For more detailed tests you can look at the
[performance section of the docs](https://prefabclasses.readthedocs.io/en/latest/perf/performance_tests.html).

## How does it work ##

The `@prefab` decorator analyses the class it is decorating and prepares an internals dict, along
with performing some other early checks (this may potentially be deferred in a future update,
**do not depend on any of the prefab internals directly**). Once this is done it sets any direct
values (`PREFAB_FIELDS` and `__match_args__` if required) and places non-data descriptors for
all of the magic methods to be generated.

The non-data descriptors for each of the magic methods perform code generation when first called
in order to generate the actual methods. Once the method has been generated, the descriptor is 
replaced on the class with the resulting method so there is no overhead regenerating the method
on each access. 

By only generating methods the first time they are used the start time can be
improved and methods that are never used don't have to be created at all (for example the 
`__repr__` method is useful when debugging but may not be used in normal runtime). In contrast
`dataclasses` generates all of its methods when the class is created.

## On using an approach vs using a tool ##

As this module's code generation is based on the workings of [David Beazley's Cluegen](https://github.com/dabeaz/cluegen)
I thought it was briefly worth discussing his note on learning an approach vs using a tool.

This project arose as a result of looking at my own approach to the same problem, based on
extending the workings of `cluegen`. I found there were some features I needed for 
the projects I was working on (the first instance being that `cluegen` doesn't support 
defaults that aren't builtins). 

This grew and on making further extensions and customising the project to my needs I found 
I wanted to use it in all of my projects and the easiest way to do this and keep things 
in sync was to publish it as a tool on PyPI.

It has only 1 dependency at runtime which is a small library I've created to handle lazy 
imports. This is used to provide easy access to functions for the user while keeping the
overall import time low. It's also used internally to defer some methods from being imported
(eg: if you never look at a `__repr__`, then you don't need to import `reprlib.recursive_repr`).
Unfortunately this raises the base import time but it's still a lot faster than `import typing`.

So this is the tool I've created for my use using the approach I've come up with to suit my needs.
You are welcome to use it if you wish - and if it suits your needs better than `attrs` or 
`dataclasses` then good. I'm glad you found this useful.
