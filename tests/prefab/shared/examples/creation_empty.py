from typing import ClassVar
from ducktools.classbuilder.prefab import prefab


@prefab
class Empty:
    pass


@prefab
class EmptyClassVars:
    x: ClassVar = 12


@prefab(iter=True)
class EmptyIter:
    pass
