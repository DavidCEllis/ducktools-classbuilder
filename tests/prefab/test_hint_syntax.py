from ducktools.classbuilder.prefab import prefab, attribute


# Tests check the __repr__
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
    file_list = attribute(default_factory=list)  # type: ignore


def test_basic_hints():
    x = Coordinates(42.0, 12.0)
    assert (x.x, x.y) == (42.0, 12.0)
    assert repr(x) == "Coordinates(x=42.0, y=12.0)"


def test_attribute_hints():
    x = Settings()
    assert repr(x) == "Settings(path='path/to/file', file_list=[])"


def test_hinted_ignored():
    # If a hinted value is given, but an unhinted value is used, all hints are ignored
    
    x = SettingsNoHint()
    assert repr(x) == "SettingsNoHint(file_list=[])"
