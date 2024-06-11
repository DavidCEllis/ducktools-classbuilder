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

## Annotation Class Usage ##

There is an additional AnnotationClass base class that allows creating slotted classes
using annotations. This has to be a base class with a specific metaclass in order to 
create the `__slots__` field *before* the class has been generated in order to work
correctly.

```python
from ducktools.classbuilder import AnnotationClass

class AnnotatedDC(AnnotationClass):
    the_answer: int = 42
    the_question: str = "What do you get if you multiply six by nine?"

    
ex = AnnotatedDC()
print(ex)
```

## Indices and tables ##

* {ref}`genindex`
* {ref}`search`
