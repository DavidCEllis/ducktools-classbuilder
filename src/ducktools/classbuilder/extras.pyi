from collections.abc import Callable
import typing

from . import Field, MethodMaker, default_methods

_T = typing.TypeVar("_T")

class PythonVersionError(Exception):
    pass


def _is_classvar(hint: object) -> bool: ...

def make_annotation_gatherer(
    field_type: type[Field] = Field,
    leave_default_values: bool = True,
) -> Callable[[type], dict[str, Field]]: ...


annotation_gatherer: Callable[[type], dict[str, Field]]

@typing.overload
def annotationclass(
    cls: type[_T],
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
) -> type[_T]: ...

@typing.overload
def annotationclass(
        cls: None = None,
        /,
        *,
        methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
) -> Callable[[type[_T]], type[_T]]: ...
