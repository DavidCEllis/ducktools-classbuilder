# Ducktools: ClassBuilder #

```{toctree}
---
maxdepth: 2
caption: "Contents:"
hidden: true
---
tutorial
extension_examples
generated_code
api
perf/performance_tests
approach_vs_tool
prefab/index
```

`ducktools-classbuilder` is *the* Python package that will bring you the **joy**
of writing... functions... that will bring back the **joy** of writing classes.

Maybe.

This specific idea came about after seeing people making multiple feature requests
to `attrs` or `dataclasses` to add features or to merge feature PRs. This project
is supposed to both provide users with some basic tools to allow them to make 
custom class generators that work with the features they need.

## A little history ##

Previously I had a project - `PrefabClasses` - which came about while getting
frustrated at the need to write converters or wrappers for multiple methods when
using `attrs`, where all I really wanted to do was coerce empty values to None 
(or the other way around).

Further development came when I started investigating CLI tools and noticed the
significant overhead of both `attrs` and `dataclasses` on import time, even before
generating any classes.

This module has largely been reimplemented as `ducktools.classbuilder.prefab` using
the tools provided by the main `classbuilder` module.

`classbuilder` and `prefab` have been intentionally written to avoid importing external
modules, including stdlib ones that would have a significant impact on start time.
(This is also why all of the typing is done in a stub file).

## Slot Class Usage ##

The building toolkit includes a basic implementation that uses
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

## Using Annotations ##

It is possible to create slotted classes using Annotations.
There is a `Prefab` base class in the `prefab` submodule that does this,
but it also easy to implement using the provided tools.

In order to correctly implement `__slots__` this needs to be done
using a metaclass as `__slots__` must be defined before the **class**
is created.

```python
from ducktools.classbuilder import (
    SlotMakerMeta,
    builder,
    check_argument_order,
    default_methods,
    unified_gatherer,
)


class AnnotationClass(metaclass=SlotMakerMeta):
    __slots__ = {}

    def __init_subclass__(
            cls,
            methods=default_methods,
            gatherer=unified_gatherer,
            **kwargs
    ):
        # Check class dict otherwise this will always be True as this base
        # class uses slots.
        slots = "__slots__" in cls.__dict__

        builder(cls, gatherer=gatherer, methods=methods, flags={"slotted": slots})
        check_argument_order(cls)
        super().__init_subclass__(**kwargs)


class AnnotatedDC(AnnotationClass):
    the_answer: int = 42
    the_question: str = "What do you get if you multiply six by nine?"


ex = AnnotatedDC()
print(ex)
```

## Indices and tables ##

* {ref}`genindex`
* {ref}`search`
