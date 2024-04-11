from ducktools.classbuilder.prefab import prefab, attribute


@prefab
class InheritObject(object):
    pass


@prefab
class Coordinate:
    x: float
    y: float


@prefab
class Coordinate3D(Coordinate):
    z = attribute()


@prefab
class CoordinateTime:
    t = attribute()


@prefab
class Coordinate4D(CoordinateTime, Coordinate3D):
    pass


@prefab
class BasePreInitPostInit:
    def __prefab_pre_init__(self):
        self.pre_init = True

    def __prefab_post_init__(self):
        self.post_init = True


@prefab
class ChildPreInitPostInit(BasePreInitPostInit):
    pass


# Multiple inheritance inconsistency test classes
# classvar and field should be equal
@prefab
class Base:
    field: int = 10
    classvar = 10


@prefab
class Child1(Base):
    pass


@prefab
class Child2(Base):
    field: int = 50
    classvar = 50


@prefab
class GrandChild(Child1, Child2):
    pass
