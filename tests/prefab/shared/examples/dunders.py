from ducktools.classbuilder.prefab import prefab, attribute


@prefab
class Coordinate:
    x: float
    y: float


@prefab
class Coordinate3D(Coordinate):
    z: float


@prefab
class CoordinateTime:
    t: float


@prefab
class Coordinate4D(CoordinateTime, Coordinate3D):
    pass


@prefab
class CoordinateNoXRepr:
    x: float = attribute(repr=False)
    y: float


@prefab
class NoXReprNoXInit:
    _type = attribute(default=None, init=False, repr=False)


@prefab(iter=True)
class CoordinateIter:
    x: float
    y: float


@prefab(match_args=False)
class NoMatchArgs:
    x: float
    y: float


@prefab
class DundersExist:
    x: int
    y: int

    __match_args__ = ("x",)

    def __init__(self, x, y):
        self.x = 2 * x
        self.y = 3 * y

    def __repr__(self):
        return "NOT_REPLACED"

    def __eq__(self, other):
        return True

    def __iter__(self):
        yield self.x
