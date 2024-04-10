"""Tests related to serialization to JSON or Pickle"""

from pathlib import PurePosixPath, PurePath

from ducktools.classbuilder.prefab import is_prefab, is_prefab_instance
from ducktools.classbuilder.prefab.funcs import as_dict, to_json
from pytest import raises


def test_is_prefab():
    from funcs_prefabs import Coordinate  # noqa

    # The Class is a prefab
    assert is_prefab(Coordinate)

    # An instance is also a prefab
    assert is_prefab(Coordinate(1, 1))


def test_is_prefab_instance():
    from funcs_prefabs import Coordinate  # noqa

    # 'Coordinate' is not a prefab instance, it is a class
    assert not is_prefab_instance(Coordinate)

    # But an instance of it is a prefab
    assert is_prefab_instance(Coordinate(1, 1))


# Serialization tests
def test_as_dict():
    from funcs_prefabs import Coordinate  # noqa

    x = Coordinate(1, 2)

    expected_dict = {"x": 1, "y": 2}

    assert as_dict(x) == expected_dict


def test_to_json():
    import json

    from funcs_prefabs import SystemPath  # noqa

    pth = SystemPath("testfile", "path/to/test")

    # Check it's a Path internally
    assert pth.path == PurePosixPath("path/to/test")
    assert as_dict(pth)["path"] == PurePosixPath("path/to/test")

    expected_json = json.dumps({"filename": "testfile", "path": "path/to/test"})
    assert to_json(pth, default=str) == expected_json

    expected_json = json.dumps({"path": "path/to/test"})
    assert to_json(pth, excludes=("filename",), default=str) == expected_json


def test_to_json_recurse():
    """Due to the implementation, json dumps should recurse by default"""
    import json

    from funcs_prefabs import Circle  # noqa

    circ = Circle()

    circ_dict = {"radius": 1, "origin": {"x": 0, "y": 0}}

    circ_json = json.dumps(circ_dict)

    assert circ_json == to_json(circ)


def test_jsonencoder_failure():
    """With the encoder for Prefabs it should still typeerror on unencodable types"""

    from funcs_prefabs import SystemPath  # noqa

    pth = SystemPath("testfile", "path/to/test")

    with raises(TypeError):
        to_json(pth)


def test_jsonencoder_layered():
    import json

    def default_for_path(o):
        if isinstance(o, PurePath):
            return str(o)
        raise TypeError(
            f"Object of type {o.__class__.__name__} is not JSON serializable"
        )

    from funcs_prefabs import SystemPath, Onion  # noqa

    pth = SystemPath("testfile", "path/to/test")
    x = Onion(pth=PurePosixPath("what"), syspath=pth)

    result = {
        "pth": "what",
        "syspath": {"filename": "testfile", "path": "path/to/test"},
    }

    assert json.dumps(result, indent=2) == to_json(
        x, default=default_for_path, indent=2
    )


def test_picklable():
    from funcs_prefabs import PicklePrefab  # noqa

    picktest = PicklePrefab()

    import pickle

    pick_dump = pickle.dumps(picktest)
    pick_restore = pickle.loads(pick_dump)

    assert pick_restore == picktest
