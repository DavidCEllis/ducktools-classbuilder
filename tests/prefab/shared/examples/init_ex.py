from ducktools.classbuilder.prefab import prefab, attribute
from pathlib import Path
from typing import Union


@prefab
class Coordinate:
    x: float
    y: float


@prefab
class CoordinateFixedY:
    x = attribute()
    y = attribute(default=2, init=False)


@prefab
class CoordinateDefaults:
    x = attribute(default=0)
    y = attribute(default=0)


@prefab
class MutableDefault:
    x = attribute(default=list())


@prefab
class FactoryDefault:
    x = attribute(default_factory=list)


@prefab
class Settings:
    """
    Global persistent settings handler
    """

    output_file = attribute(default=Path("Settings.json"))


@prefab
class PreInitExample:
    init_value: bool = True

    def __prefab_pre_init__(self):
        self.pre_init_ran = True


@prefab
class PostInitExample:
    init_value: bool = True

    def __prefab_post_init__(self):
        self.post_init_ran = True


@prefab
class PrePostInitArguments:
    x: int = 1
    y: int = 2

    def __prefab_pre_init__(self, x, y):
        if x > y:
            raise ValueError("X must be less than Y")

    def __prefab_post_init__(self, x, y):
        self.x = 2 * x
        self.y = 3 * y


@prefab
class ExcludeField:
    x = attribute(default="excluded_field", exclude_field=True)

    def __prefab_post_init__(self, x):
        self.x = x.upper()


@prefab
class PostInitPartial:
    x: int
    y: int
    z: "list[int]" = attribute(default_factory=list)

    def __prefab_post_init__(self, z):
        z.append(1)
        self.z = z


@prefab
class PostInitAnnotations:
    x: int
    y: Path

    def __prefab_post_init__(self, y: Union[str, Path]):
        self.y = Path(y)


@prefab
class EmptyContainers:
    x: list = attribute(default_factory=list)
    y: set = attribute(default_factory=set)
    z: dict = attribute(default_factory=dict)


@prefab
class TypeSignatureInit:
    x: int
    y: str = "Test"


@prefab
class PartialTypeSignatureInit:
    x = attribute()
    y: str = attribute(default="Test")
