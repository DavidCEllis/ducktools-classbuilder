import typing
from types import MappingProxyType
from typing_extensions import dataclass_transform

import inspect

from collections.abc import Callable

from . import (
    NOTHING,
    Field,
    GeneratedCode,
    MethodMaker,
    SlotMakerMeta,
)

from . import SlotFields as SlotFields, KW_ONLY as KW_ONLY

# noinspection PyUnresolvedReferences
from . import _NothingType

PREFAB_FIELDS: str
PREFAB_INIT_FUNC: str
PRE_INIT_FUNC: str
POST_INIT_FUNC: str

_CopiableMappings = dict[str, typing.Any] | MappingProxyType[str, typing.Any]

class PrefabError(Exception): ...

def get_attributes(cls: type) -> dict[str, Attribute]: ...

def init_generator(cls: type, funcname: str = "__init__") -> GeneratedCode: ...
def iter_generator(cls: type, funcname: str = "__iter__") -> GeneratedCode: ...
def as_dict_generator(cls: type, funcname: str = "as_dict") -> GeneratedCode: ...
def hash_generator(cls: type, funcname: str = "__hash__") -> GeneratedCode: ...

init_maker: MethodMaker
prefab_init_maker: MethodMaker
repr_maker: MethodMaker
recursive_repr_maker: MethodMaker
eq_maker: MethodMaker
iter_maker: MethodMaker
asdict_maker: MethodMaker
hash_maker: MethodMaker

class Attribute(Field):
    __slots__: dict
    __signature__: inspect.Signature

    iter: bool
    serialize: bool

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
    private: bool = False,
) -> Attribute: ...

def prefab_gatherer(cls_or_ns: type | MappingProxyType) -> tuple[dict[str, Attribute], dict[str, typing.Any]]: ...

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

# noinspection PyUnresolvedReferences
@dataclass_transform(field_specifiers=(Attribute, attribute))
class Prefab(metaclass=SlotMakerMeta):
    _meta_gatherer: Callable[[type | _CopiableMappings], tuple[dict[str, Field], dict[str, typing.Any]]]
    def __init_subclass__(
        cls,
        init: bool = True,
        repr: bool = True,
        eq: bool = True,
        iter: bool = False,
        match_args: bool = True,
        kw_only: bool = False,
        frozen: bool = False,
        dict_method: bool = False,
        recursive_repr: bool = False,
    ) -> None: ...


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
