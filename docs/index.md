# Ducktools: ClassBuilder #

```{toctree}
---
maxdepth: 2
caption: "Contents:"
hidden: true
---
extension_examples
api
prefab/index
prefab/api
perf/performance_tests
```

`ducktools-classbuilder` is *the* Python package that will bring you the **joy**
of writing... **functions that write classes**.

Maybe that's just me.

This specific idea came about after seeing people making multiple feature requests
to `attrs` or `dataclasses` to add features or to merge feature PRs. This project
is supposed to both provide users with some basic tools to allow them to make 
custom class generators that work with the features they need.

Previously I had a project - `PrefabClasses` - which came about while getting
frustrated at the need to write converters or wrappers for multiple methods when
using `attrs`, where all I really wanted to do was coerce empty values to None 
(or the other way around).

Further development came when I started investigating CLI tools and noticed the
significant overhead of both `attrs` and `dataclasses` on import time, even before
generating any classes.

`classbuilder` and `prefab` have been intentionally written to avoid importing external
modules, including stdlib ones that would have a significant impact on start time.
(This is why all of the typing is done in a stub file).

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `python -c "pass"` | 12.7 ± 1.5 | 11.4 | 16.7 | 1.00 |
| `python -c "from ducktools.classbuilder import slotclass"` | 13.6 ± 1.6 | 12.0 | 18.1 | 1.08 ± 0.18 |
| `python -c "from ducktools.classbuilder.prefab import prefab"` | 14.6 ± 2.5 | 12.5 | 21.4 | 1.16 ± 0.24 |
| `python -c "from collections import namedtuple"` | 16.4 ± 2.2 | 13.7 | 22.5 | 1.29 ± 0.23 |
| `python -c "from typing import NamedTuple"` | 29.0 ± 4.3 | 23.2 | 38.7 | 2.29 ± 0.43 |
| `python -c "from dataclasses import dataclass"` | 37.2 ± 3.6 | 32.1 | 46.7 | 2.93 ± 0.44 |
| `python -c "from attrs import define"` | 63.9 ± 7.7 | 54.7 | 79.8 | 5.04 ± 0.85 |
| `python -c "from pydantic import BaseModel"` | 93.4 ± 12.0 | 78.8 | 117.3 | 7.38 ± 1.28 |

## Indices and tables ##

* {ref}`genindex`
* {ref}`search`
