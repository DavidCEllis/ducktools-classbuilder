import typing

from collections.abc import Callable
from typing_extensions import dataclass_transform

from . import Field, MethodMaker, default_methods

_T = typing.TypeVar("_T")


def eval_hint(
    hint: object,
    obj_globals: None | dict[str, typing.Any] = None,
    obj_locals: None | dict[str, typing.Any] = None,
) -> object: ...

def is_classvar(
    hint: object,
) -> bool: ...


class SlotMakerMeta(type):
    def __new__(
        cls: type[_T],
        name: str,
        bases: tuple[type, ...],
        ns: dict[str, typing.Any],
        slots: bool = True,
        **kwargs: typing.Any,
    ) -> _T: ...

def make_annotation_gatherer(
    field_type: type[Field] = Field,
    leave_default_values: bool = True,
) -> Callable[[type], tuple[dict[str, Field], dict[str, typing.Any]]]: ...

def annotation_gatherer(cls: type) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...


@dataclass_transform(field_specifiers=(Field,))
class AnnotationClass(metaclass=SlotMakerMeta):
    def __init_subclass__(
        cls,
        methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
        **kwargs,
    ) -> None: ...
