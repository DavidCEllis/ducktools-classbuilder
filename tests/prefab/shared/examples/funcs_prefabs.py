from ducktools.classbuilder.prefab import prefab, attribute
from pathlib import Path, PurePosixPath


@prefab
class Coordinate:
    x: float
    y: float


@prefab
class Circle:
    radius = attribute(default=1)
    origin = attribute(default=Coordinate(0, 0))


@prefab
class SystemPath:
    filename = attribute()
    path = attribute()

    def __prefab_post_init__(self, path):
        self.path = PurePosixPath(path)


@prefab
class Onion:
    pth: PurePosixPath
    syspath: SystemPath


@prefab
class PicklePrefab:
    x = attribute(default=800)
    y = attribute(default=Path("Settings.json"))
