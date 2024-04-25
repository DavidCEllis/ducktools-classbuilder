# Performance tests #

Rough specs: 2023 Windows 10 Desktop: Intel i5-13600KF, Crucial P3 1TB PCIe M.2 2280 SSD

## Import Times ##

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `python -c "pass"` | 23.2 ± 0.8 | 21.8 | 25.3 | 1.00 |
| `python -c "from ducktools.classbuilder import slotclass"` | 23.4 ± 1.8 | 22.3 | 32.8 | 1.01 ± 0.09 |
| `python -c "from ducktools.classbuilder.prefab import prefab"` | 23.7 ± 0.9 | 22.8 | 27.6 | 1.02 ± 0.05 |
| `python -c "from collections import namedtuple"` | 24.2 ± 0.8 | 23.3 | 27.5 | 1.04 ± 0.05 |
| `python -c "from typing import NamedTuple"` | 32.2 ± 0.8 | 30.7 | 35.7 | 1.39 ± 0.06 |
| `python -c "from dataclasses import dataclass"` | 39.6 ± 1.1 | 37.9 | 43.2 | 1.70 ± 0.08 |
| `python -c "from attrs import define"` | 54.0 ± 1.8 | 51.4 | 60.1 | 2.32 ± 0.11 |
| `python -c "from pydantic import BaseModel"` | 70.2 ± 1.2 | 68.3 | 72.7 | 3.02 ± 0.12 |



## Loading a module with 100 classes defined ##

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `python -c "pass"` | 22.9 ± 0.4 | 21.8 | 23.6 | 1.00 |
| `python hyperfine_importers/native_classes_timer.py` | 24.2 ± 0.7 | 22.8 | 26.6 | 1.06 ± 0.04 |
| `python hyperfine_importers/slotclasses_timer.py` | 24.9 ± 0.7 | 23.8 | 27.7 | 1.09 ± 0.04 |
| `python hyperfine_importers/prefab_timer.py` | 25.8 ± 0.5 | 24.8 | 27.2 | 1.13 ± 0.03 |
| `python hyperfine_importers/prefab_slots_timer.py` | 25.9 ± 0.6 | 24.9 | 27.5 | 1.13 ± 0.03 |
| `python hyperfine_importers/prefab_eval_timer.py` | 35.1 ± 0.6 | 34.0 | 36.4 | 1.53 ± 0.04 |
| `python hyperfine_importers/namedtuples_timer.py` | 28.3 ± 0.4 | 27.5 | 29.0 | 1.24 ± 0.03 |
| `python hyperfine_importers/typed_namedtuples_timer.py` | 39.1 ± 0.9 | 37.4 | 41.8 | 1.71 ± 0.05 |
| `python hyperfine_importers/dataclasses_timer.py` | 61.1 ± 2.1 | 58.1 | 69.1 | 2.67 ± 0.11 |
| `python hyperfine_importers/attrs_noslots_timer.py` | 88.9 ± 2.2 | 86.7 | 98.3 | 3.88 ± 0.12 |
| `python hyperfine_importers/attrs_slots_timer.py` | 90.9 ± 1.4 | 88.9 | 94.2 | 3.97 ± 0.10 |
| `python hyperfine_importers/pydantic_timer.py` | 172.4 ± 5.3 | 164.5 | 181.5 | 7.53 ± 0.27 |



## Class Generation time without imports ##

From `perf_profile.py`.

```
Python Version: 3.12.2 (tags/v3.12.2:6abddd9, Feb  6 2024, 21:26:36) [MSC v.1937 64 bit (AMD64)]
Classbuilder version: v0.4.0
Platform: Windows-10-10.0.19045-SP0
Time for 100 imports of 100 classes defined with 5 basic attributes
```

| Method | Total Time (seconds) |
| --- | --- |
| standard classes | 0.07 |
| namedtuple | 0.33 |
| NamedTuple | 0.50 |
| dataclasses | 2.05 |
| attrs 23.2.0 | 3.73 |
| pydantic 2.7.1 | 4.19 |
| dabeaz/cluegen | 0.10 |
| dabeaz/cluegen_eval | 0.91 |
| dabeaz/dataklasses | 0.10 |
| dabeaz/dataklasses_eval | 0.10 |
| slotclass v0.4.0 | 0.12 |
| prefab_slots v0.4.0 | 0.16 |
| prefab v0.4.0 | 0.18 |
| prefab_attributes v0.4.0 | 0.16 |
| prefab_eval v0.4.0 | 1.12 |
