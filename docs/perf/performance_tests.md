# Performance tests #

Rough specs: 2023 Windows 10 Desktop: Intel i5-13600KF, Crucial P3 1TB PCIe M.2 2280 SSD

## Notes on comparisons ##

The main goal for comparison here is with `dataclasses`, but other modules are included in the 
comparisons as they all implement some kind of boilerplate writing for classes.

`Pydantic` does a lot of additional work with regard to data validation. If you require validation
then it doesn't matter what the performance difference here is, you need Pydantic.

`attrs` takes a different approach to some features which some users may prefer. If you need these
features, use attrs.

## Import Times ##

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `python -c "pass"` | 22.5 ± 0.5 | 21.2 | 23.3 | 1.00 |
| `python -c "from ducktools.classbuilder import slotclass"` | 22.7 ± 0.3 | 22.3 | 23.3 | 1.01 ± 0.03 |
| `python -c "from ducktools.classbuilder.prefab import prefab"` | 23.2 ± 0.4 | 22.5 | 24.3 | 1.03 ± 0.03 |
| `python -c "from collections import namedtuple"` | 23.6 ± 0.3 | 23.1 | 24.3 | 1.05 ± 0.03 |
| `python -c "from typing import NamedTuple"` | 31.3 ± 0.4 | 30.5 | 32.3 | 1.39 ± 0.04 |
| `python -c "from dataclasses import dataclass"` | 38.2 ± 0.6 | 37.3 | 40.7 | 1.70 ± 0.05 |
| `python -c "from attrs import define"` | 52.3 ± 1.1 | 51.1 | 55.8 | 2.33 ± 0.07 |
| `python -c "from pydantic import BaseModel"` | 69.3 ± 1.6 | 67.3 | 75.0 | 3.09 ± 0.10 |



## Loading a module with 100 classes defined ##

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `python -c "pass"` | 22.3 ± 0.6 | 21.4 | 23.6 | 1.00 |
| `python hyperfine_importers/native_classes_timer.py` | 23.3 ± 0.4 | 22.6 | 24.0 | 1.04 ± 0.03 |
| `python hyperfine_importers/slotclasses_timer.py` | 25.1 ± 0.3 | 24.5 | 25.7 | 1.12 ± 0.03 |
| `python hyperfine_importers/prefab_timer.py` | 26.0 ± 0.5 | 25.3 | 28.0 | 1.16 ± 0.04 |
| `python hyperfine_importers/prefab_slots_timer.py` | 25.9 ± 0.5 | 25.1 | 28.3 | 1.16 ± 0.04 |
| `python hyperfine_importers/prefab_eval_timer.py` | 37.6 ± 2.3 | 35.4 | 47.7 | 1.68 ± 0.11 |
| `python hyperfine_importers/namedtuples_timer.py` | 28.0 ± 0.4 | 27.0 | 28.6 | 1.25 ± 0.04 |
| `python hyperfine_importers/typed_namedtuples_timer.py` | 37.9 ± 0.8 | 36.9 | 39.8 | 1.70 ± 0.06 |
| `python hyperfine_importers/dataclasses_timer.py` | 60.1 ± 1.1 | 58.1 | 62.6 | 2.69 ± 0.08 |
| `python hyperfine_importers/attrs_noslots_timer.py` | 87.1 ± 1.0 | 85.3 | 88.7 | 3.90 ± 0.11 |
| `python hyperfine_importers/attrs_slots_timer.py` | 89.2 ± 1.0 | 87.7 | 91.8 | 4.00 ± 0.11 |
| `python hyperfine_importers/pydantic_timer.py` | 168.4 ± 3.6 | 161.0 | 177.7 | 7.54 ± 0.25 |


## Class Generation time without imports ##

From `perf_profile.py`.

```
Python Version: 3.12.3 (tags/v3.12.3:f6650f9, Apr  9 2024, 14:05:25) [MSC v.1938 64 bit (AMD64)]
Classbuilder version: v0.6.0
Platform: Windows-10-10.0.19045-SP0
Time for 100 imports of 100 classes defined with 5 basic attributes
```

| Method | Total Time (seconds) |
| --- | --- |
| standard classes | 0.07 |
| namedtuple | 0.33 |
| NamedTuple | 0.49 |
| dataclasses | 2.03 |
| attrs 23.2.0 | 3.52 |
| pydantic 2.7.3 | 4.04 |
| dabeaz/cluegen | 0.09 |
| dabeaz/cluegen_eval | 0.86 |
| dabeaz/dataklasses | 0.09 |
| dabeaz/dataklasses_eval | 0.09 |
| slotclass v0.6.0 | 0.14 |
| prefab_slots v0.6.0 | 0.18 |
| prefab v0.6.0 | 0.21 |
| prefab_attributes v0.6.0 | 0.18 |
| prefab_eval v0.6.0 | 1.15 |
