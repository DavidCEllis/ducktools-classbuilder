from ducktools.classbuilder.prefab import prefab, attribute
from pathlib import Path


@prefab
class Coordinate:
    x: float
    y: float


@prefab(dict_method=True)
class CachedCoordinate:
    x: float
    y: float


@prefab
class PicklePrefab:
    x = attribute(default=800)
    y = attribute(default=Path("Settings.json"))
