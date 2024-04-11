import pytest


def test_basic_frozen():
    from frozen_prefabs import FrozenExample

    # Make sure basics still work
    x = FrozenExample(x=0)
    assert x.x == 0
    assert x.y == "Example Data"
    assert x.z == []

    with pytest.raises(TypeError) as e1:
        x.x = 2

    assert (
        e1.value.args[0]
        == "'FrozenExample' object does not support attribute assignment"
    )

    with pytest.raises(TypeError) as e2:
        x.y = "Fail to change data"

    assert x.x == 0
    assert x.y == "Example Data"


def test_mutable_default():
    from frozen_prefabs import FrozenExample

    base_list = []

    x = FrozenExample(x=0, y="New Data", z=base_list)

    assert x.x == 0
    assert x.y == "New Data"
    assert x.z is base_list

    new_base_list = []

    with pytest.raises(TypeError) as e1:
        x.z = new_base_list

    assert x.z is not new_base_list
    assert x.z is base_list


def test_delete_blocked():
    from frozen_prefabs import FrozenExample

    x = FrozenExample(x=0)

    with pytest.raises(TypeError) as e:
        del x.x

    assert (
        e.value.args[0] == "'FrozenExample' object does not support attribute deletion"
    )

    assert x.x == 0
