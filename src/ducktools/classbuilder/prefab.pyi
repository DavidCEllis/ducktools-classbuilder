import typing
from typing_extensions import dataclass_transform

from collections.abc import Callable

from . import (
    INTERNALS_DICT, NOTHING,
    Field, MethodMaker, SlotFields as SlotFields,
    builder, get_flags, get_fields, make_slot_gatherer
)

# noinspection PyUnresolvedReferences
from . import _NothingType

PREFAB_FIELDS: str
PREFAB_INIT_FUNC: str
PRE_INIT_FUNC: str
POST_INIT_FUNC: str


# noinspection PyPep8Naming
class _KW_ONLY_TYPE:
    def __repr__(self) -> str: ...

KW_ONLY: _KW_ONLY_TYPE

class PrefabError(Exception): ...

def get_attributes(cls: type) -> dict[str, Attribute]: ...

def get_init_maker(*, init_name: str="__init__") -> MethodMaker: ...

def get_repr_maker(*, recursion_safe: bool = False) -> MethodMaker: ...

def get_eq_maker() -> MethodMaker: ...

def get_iter_maker() -> MethodMaker: ...

def get_asdict_maker() -> MethodMaker: ...


init_maker: MethodMaker
prefab_init_maker: MethodMaker
repr_maker: MethodMaker
recursive_repr_maker: MethodMaker
eq_maker: MethodMaker
iter_maker: MethodMaker
asdict_maker: MethodMaker

class Attribute(Field):
    __slots__: dict

    iter: bool
    serialize: bool
    exclude_field: bool

    def __init__(
        self,
        *,
        default: typing.Any | _NothingType = NOTHING,
        default_factory: typing.Any | _NothingType = NOTHING,
        type: type | _NothingType = NOTHING,
        doc: str | None = None,
        init: bool = True,
        repr: bool = True,
        compare: bool = True,
        iter: bool = True,
        kw_only: bool = False,
        serialize: bool = True,
        exclude_field: bool = False,
    ) -> None: ...

    def __repr__(self) -> str: ...
    def __eq__(self, other: Attribute | object) -> bool: ...
    def validate_field(self) -> None: ...

def attribute(
    *,
    default: typing.Any | _NothingType = NOTHING,
    default_factory: typing.Any | _NothingType = NOTHING,
    type: type | _NothingType = NOTHING,
    doc: str | None = None,
    init: bool = True,
    repr: bool = True,
    compare: bool = True,
    iter: bool = True,
    kw_only: bool = False,
    serialize: bool = True,
    exclude_field: bool = False,
) -> Attribute: ...

def slot_prefab_gatherer(cls: type) -> tuple[dict[str, Attribute], dict[str, typing.Any]]: ...

def attribute_gatherer(cls: type) -> tuple[dict[str, Attribute], dict[str, typing.Any]]: ...

def _make_prefab(
    cls: type,
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    iter: bool = False,
    match_args: bool = True,
    kw_only: bool = False,
    frozen: bool = False,
    dict_method: bool = False,
    recursive_repr: bool = False,
    gathered_fields: Callable[[type], tuple[dict[str, Attribute], dict[str, typing.Any]]] | None = None,
) -> type: ...

_T = typing.TypeVar("_T")


# For some reason PyCharm can't see 'attribute'?!?
# noinspection PyUnresolvedReferences
@dataclass_transform(field_specifiers=(Attribute, attribute))
def prefab(
    cls: type[_T] | None = None,
    *,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    iter: bool = False,
    match_args: bool = True,
    kw_only: bool = False,
    frozen: bool = False,
    dict_method: bool = False,
    recursive_repr: bool = False,
) -> type[_T] | Callable[[type[_T]], type[_T]]: ...

def build_prefab(
    class_name: str,
    attributes: list[tuple[str, Attribute]],
    *,
    bases: tuple[type, ...] = (),
    class_dict: dict[str, typing.Any] | None = None,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
    iter: bool = False,
    match_args: bool = True,
    kw_only: bool = False,
    frozen: bool = False,
    dict_method: bool = False,
    recursive_repr: bool = False,
    slots: bool = False,
) -> type: ...

def is_prefab(o: typing.Any) -> bool: ...

def is_prefab_instance(o: object) -> bool: ...

def as_dict(o) -> dict[str, typing.Any]: ...
