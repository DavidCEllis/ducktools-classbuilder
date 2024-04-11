from ducktools.classbuilder.prefab import prefab, attribute


@prefab
class FailSyntax:
    x = attribute(default=0)
    y = attribute()
