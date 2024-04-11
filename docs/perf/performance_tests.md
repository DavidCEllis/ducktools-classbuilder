# Performance tests #

Currently from an aging Dell XPS13 laptop running ubuntu 22.04 and Python 3.12.2.
Windows tests with detailed specs soon.

## Import Times ##

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `python -c "pass"` | 12.2 ± 1.0 | 11.2 | 15.2 | 1.00 |
| `python -c "from ducktools.classbuilder import slotclass"` | 12.6 ± 1.0 | 11.8 | 15.0 | 1.03 ± 0.12 |
| `python -c "from ducktools.classbuilder.prefab import prefab"` | 13.0 ± 0.8 | 12.3 | 15.7 | 1.06 ± 0.11 |
| `python -c "from collections import namedtuple"` | 14.0 ± 0.7 | 13.3 | 15.9 | 1.15 ± 0.11 |
| `python -c "from typing import NamedTuple"` | 23.5 ± 1.0 | 22.3 | 25.7 | 1.92 ± 0.18 |
| `python -c "from dataclasses import dataclass"` | 32.8 ± 1.0 | 30.9 | 35.4 | 2.69 ± 0.23 |
| `python -c "from attrs import define"` | 50.9 ± 1.3 | 48.4 | 53.9 | 4.17 ± 0.35 |
| `python -c "from pydantic import BaseModel"` | 75.9 ± 1.3 | 73.8 | 80.9 | 6.22 ± 0.51 |

## Loading a module with 100 classes defined ##

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `python -c "pass"` | 11.6 ± 0.6 | 11.2 | 12.8 | 1.00 |
| `python hyperfine_importers/native_classes_timer.py` | 13.9 ± 0.8 | 13.1 | 15.6 | 1.20 ± 0.09 |
| `python hyperfine_importers/slotclasses_timer.py` | 15.0 ± 0.6 | 14.3 | 16.4 | 1.29 ± 0.08 |
| `python hyperfine_importers/prefab_timer.py` | 16.9 ± 0.7 | 16.0 | 18.7 | 1.45 ± 0.09 |
| `python hyperfine_importers/prefab_slots_timer.py` | 16.7 ± 0.7 | 15.8 | 17.8 | 1.43 ± 0.09 |
| `python hyperfine_importers/prefab_eval_timer.py` | 41.0 ± 1.5 | 39.2 | 44.6 | 3.52 ± 0.21 |
| `python hyperfine_importers/namedtuples_timer.py` | 22.3 ± 1.2 | 21.2 | 26.7 | 1.92 ± 0.14 |
| `python hyperfine_importers/typed_namedtuples_timer.py` | 38.0 ± 1.2 | 36.2 | 41.3 | 3.27 ± 0.19 |
| `python hyperfine_importers/dataclasses_timer.py` | 77.3 ± 3.5 | 74.5 | 93.1 | 6.65 ± 0.44 |
| `python hyperfine_importers/attrs_noslots_timer.py` | 119.9 ± 1.6 | 117.1 | 122.5 | 10.32 ± 0.51 |
| `python hyperfine_importers/attrs_slots_timer.py` | 123.4 ± 2.1 | 119.5 | 131.6 | 10.62 ± 0.54 |
| `python hyperfine_importers/pydantic_timer.py` | 275.6 ± 6.3 | 267.8 | 304.8 | 23.72 ± 1.25 |

## Class Generation time without imports ##

From `perf_profile.py`.

```
Python Version: 3.12.1 (main, Dec 10 2023, 09:30:46) [GCC 11.4.0]
Classbuilder version: v0.1.0
Platform: Linux-5.15.0-91-generic-x86_64-with-glibc2.35
Time for 100 imports of 100 classes defined with 5 basic attributes
```

| Method | Total Time (seconds) |
| --- | --- |
| standard classes | 0.13 |
| namedtuple | 0.72 |
| NamedTuple | 1.29 |
| dataclasses | 4.24 |
| attrs 23.2.0 | 7.04 |
| pydantic 2.6.4 | 10.25 |
| dabeaz/cluegen | 0.28 |
| dabeaz/cluegen_eval | 2.50 |
| dabeaz/dataklasses | 0.27 |
| dabeaz/dataklasses_eval | 0.27 |
| slotclass v0.1.0 | 0.28 |
| prefab_slots v0.1.0 | 0.38 |
| prefab v0.1.0 | 0.38 |
| prefab_attributes v0.1.0 | 0.40 |
| prefab_eval v0.1.0 | 2.98 |
