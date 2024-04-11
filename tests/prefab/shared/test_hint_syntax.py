def test_basic_hints():
    from hint_syntax import Coordinates

    x = Coordinates(42.0, 12.0)
    assert (x.x, x.y) == (42.0, 12.0)
    assert repr(x) == "Coordinates(x=42.0, y=12.0)"


def test_attribute_hints():
    from hint_syntax import Settings

    x = Settings()
    assert repr(x) == "Settings(path='path/to/file', file_list=[])"


def test_hinted_ignored():
    # If a hinted value is given, but an unhinted value is used, all hints are ignored
    from hint_syntax import SettingsNoHint

    x = SettingsNoHint()
    assert repr(x) == "SettingsNoHint(file_list=[])"
