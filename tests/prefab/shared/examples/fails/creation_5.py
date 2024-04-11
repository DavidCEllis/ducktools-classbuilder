from ducktools.classbuilder.prefab import prefab, attribute


@prefab
class Construct:
    x = attribute(default=12, default_factory=list)
