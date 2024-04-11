from ducktools.classbuilder.prefab import prefab, attribute


@prefab
class RegularRepr:
    x: str = "Hello"
    y: str = "World"


@prefab
class NoReprAttributes:
    x: str = attribute(default="Hello", repr=False)
    y: str = attribute(default="World", repr=False)


@prefab
class OneAttributeNoRepr:
    x: str = attribute(default="Hello", repr=False)
    y: str = "World"


@prefab
class OneAttributeNoInit:
    x: str = "Hello"
    y: str = attribute(default="World", init=False)


@prefab
class OneAttributeExcludeField:
    x: str = "Hello"
    y: str = attribute(default="World", exclude_field=True)

    def __prefab_post_init__(self, y):
        self.y = y


@prefab
class RegularReprOneArg:
    x: str = "Hello"
    y: str = attribute(default="World", init=False, repr=False)


@prefab(recursive_repr=True)
class RecursiveObject:
    x: "RecursiveObject | None" = None
