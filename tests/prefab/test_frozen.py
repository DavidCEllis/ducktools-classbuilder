import pytest

from ducktools.classbuilder.prefab import Prefab, prefab, attribute


@prefab(frozen=True)
class FrozenContents:
    x: int
    y: str = "Example Data"


@prefab(frozen=True)
class FrozenMutableContents:
    x: int
    y: str = "Example Data"
    z: list = attribute(default_factory=list)


def test_basic_frozen():
    # Make sure basics still work
    x = FrozenMutableContents(x=0)
    assert x.x == 0
    assert x.y == "Example Data"
    assert x.z == []

    with pytest.raises(TypeError) as e1:
        x.x = 2

    assert (
        e1.value.args[0]
        == "'FrozenMutableContents' object does not support attribute assignment"
    )

    with pytest.raises(TypeError) as e2:
        x.y = "Fail to change data"

    assert x.x == 0
    assert x.y == "Example Data"


def test_mutable_default():

    base_list = []

    x = FrozenMutableContents(x=0, y="New Data", z=base_list)

    assert x.x == 0
    assert x.y == "New Data"
    assert x.z is base_list

    new_base_list = []

    with pytest.raises(TypeError) as e1:
        x.z = new_base_list

    assert x.z is not new_base_list
    assert x.z is base_list


def test_delete_blocked():

    x = FrozenMutableContents(x=0)

    with pytest.raises(TypeError) as e:
        del x.x

    assert (
        e.value.args[0] == "'FrozenMutableContents' object does not support attribute deletion"
    )

    assert x.x == 0


def test_hash_unfrozen():
    @prefab(eq=False)
    class Hashable:
        x: int
        y: str = "Example Data"

    @prefab(frozen=False)
    class Unhashable:
        x: int
        y: str = "Example Data"

    hashable = Hashable(x=0)
    unhashable = Unhashable(x=0)

    hash(hashable)

    with pytest.raises(TypeError):
        hash(unhashable)


def test_hash_already_exists():
    @prefab
    class HashableMutable:
        x: int
        y: str = "Example Data"

        def __hash__(self):
            return hash(self.x)

    @prefab(frozen=True)
    class HashableImmutable:
        x: int
        y: str = "Example Data"

        def __hash__(self):
            return hash(self.x)

    mut = HashableMutable(42)
    immut = HashableImmutable(42)

    assert hash(mut) == hash(42)
    assert hash(immut) == hash(42)

    # Unfrozen subclass should have hash removed
    @prefab
    class MutableSub(HashableMutable):
        pass

    mut_sub = MutableSub(42)

    with pytest.raises(TypeError):
        hash(mut_sub)

    # Frozen subclass should still get a new __hash__ method
    @prefab(frozen=True)
    class ImmutSub(HashableImmutable):
        pass

    sub = ImmutSub(42)

    assert hash(sub) == hash((42, "Example Data"))


def test_inherit():
    # Test mutable classes can't inherit from immutable classes
    @prefab(frozen=True)
    class Base:
        a: int = 42

    with pytest.raises(TypeError):
        @prefab(frozen=False)
        class Sub(Base):  # type: ignore
            pass

    # And with the base class
    class BaseSlot(Prefab, frozen=True):
        a: int = 42

    with pytest.raises(TypeError):
        class SubSlot(BaseSlot, frozen=False):  # type: ignore
            pass


def test_hashable():
    ex = FrozenContents(x=0)
    hash(ex)

    ex2 = FrozenMutableContents(x=0)
    with pytest.raises(TypeError):
        hash(ex2)


def test_hash_keys():
    ex = FrozenContents(x=0, y="")
    ex_copy = FrozenContents(x=0, y="")

    ex_different_x = FrozenContents(x=1, y="")
    ex_different_y = FrozenContents(x=0, y="Different")

    ex_dict = {
        ex: ex,
    }

    assert ex in ex_dict
    assert ex_dict[ex] is ex
    assert ex_dict[ex_copy] is ex
    assert ex_different_x not in ex_dict
    assert ex_different_y not in ex_dict
