from ducktools.classbuilder.prefab import prefab, attribute


@prefab
class Coordinates:
    x: float
    y: float


@prefab
class Settings:
    path: str = "path/to/file"
    file_list: list = attribute(default_factory=list)


@prefab
class SettingsNoHint:
    path: str = "path/to/file"
    file_list = attribute(default_factory=list)
