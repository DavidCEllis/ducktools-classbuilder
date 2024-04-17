"""Tests related to serialization to JSON or Pickle"""

from ducktools.classbuilder.prefab import prefab, attribute, SlotFields
from ducktools.classbuilder.prefab import is_prefab, is_prefab_instance, as_dict


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
    from funcs_prefabs import Coordinate, CachedCoordinate  # noqa

    x = Coordinate(1, 2)

    expected_dict = {"x": 1, "y": 2}

    assert as_dict(x) == expected_dict

    y = CachedCoordinate(1, 2)

    assert hasattr(y, "as_dict")

    assert as_dict(y) == expected_dict


def test_as_dict_excludes():
    @prefab
    class ExcludesUncached:
        name: str
        password: str = attribute(serialize=False)

    @prefab(dict_method=True)
    class ExcludesCached:
        name: str
        password: str = attribute(serialize=False)

    @prefab(dict_method=True)
    class ExcludesSlots:
        __slots__ = SlotFields(
            name=attribute(type=str),
            password=attribute(serialize=False, type=str)
        )

    @prefab(dict_method=True)
    class ExcludeSpecific:
        __slots__ = SlotFields(
            name=attribute(type=str),
            password=attribute(exclude_field=True, type=str)
        )

        def __prefab_post_init__(self, password):
            self.password = password

    user1 = ExcludesUncached("Boris", "chair")
    user2 = ExcludesCached("Skroob", "1 2 3 4 5")
    user3 = ExcludesSlots("user", "password")
    user4 = ExcludeSpecific("user", "password")

    user1_out = {"name": "Boris"}
    user2_out = {"name": "Skroob"}
    user3_out = {"name": "user"}
    user4_out = {"name": "user"}

    assert as_dict(user1) == user1_out
    assert as_dict(user2) == user2_out
    assert as_dict(user3) == user3_out
    assert as_dict(user4) == user4_out

def test_picklable():
    from funcs_prefabs import PicklePrefab  # noqa

    picktest = PicklePrefab()

    import pickle

    pick_dump = pickle.dumps(picktest)
    pick_restore = pickle.loads(pick_dump)

    assert pick_restore == picktest
