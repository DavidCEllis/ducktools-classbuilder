from ducktools.classbuilder.prefab import prefab, attribute, KW_ONLY


@prefab
class KWBasic:
    x = attribute(kw_only=True)
    y = attribute(kw_only=True)


@prefab
class KWOrdering:
    x = attribute(default=2, kw_only=True)
    y = attribute()


@prefab
class KWBase:
    x = attribute(default=2, kw_only=True)


@prefab
class KWChild(KWBase):
    y = attribute()


@prefab(kw_only=True)
class KWPrefabArgument:
    x = attribute()
    y = attribute()


@prefab(kw_only=True)
class KWPrefabArgumentOverrides:
    x = attribute()
    y = attribute(kw_only=False)


@prefab
class KWFlagNoDefaults:
    x: int
    _: KW_ONLY
    y: int


@prefab
class KWFlagXDefault:
    x: int = 1
    _: KW_ONLY
    y: int
