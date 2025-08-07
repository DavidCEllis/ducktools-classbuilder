import typing
from types import MappingProxyType
from typing_extensions import dataclass_transform

import inspect

# Suppress weird pylance error
from collections.abc import Callable  # type: ignore

from . import (
    NOTHING,
    Field,
    GeneratedCode,
    MethodMaker,
    SlotMakerMeta,
    _SignatureMaker
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
    __signature__: _SignatureMaker
    __classbuilder_gathered_fields__: tuple[dict[str, Field], dict[str, typing.Any]]

    iter: bool
    serialize: bool
    metadata: dict

    def __init__(
        self,
        *,
        default: typing.Any | _NothingType = NOTHING,
        default_factory: typing.Any | _NothingType = NOTHING,
        type: type | _NothingType = NOTHING,
        doc: str | None = ...,
        init: bool = ...,
        repr: bool = ...,
        compare: bool = ...,
        iter: bool = ...,
        kw_only: bool = ...,
        serialize: bool = ...,
        metadata: dict | None = ...,
    ) -> None: ...

    def __repr__(self) -> str: ...
    def __eq__(self, other: Attribute | object) -> bool: ...
    def validate_field(self) -> None: ...

@typing.overload
def attribute(
    *,
    default: _T,
    default_factory: _NothingType = NOTHING,
    init: bool = ...,
    repr: bool = ...,
    compare: bool = ...,
    iter: bool = ...,
    kw_only: bool = ...,
    serialize: bool = ...,
    exclude_field: bool = ...,
    private: bool = ...,
    doc: str | None = ...,
    metadata: dict | None = ...,
    type: type | _NothingType = ...,
) -> _T: ...

@typing.overload
def attribute(
    *,
    default: _NothingType = NOTHING,
    default_factory: Callable[[], _T],
    init: bool = ...,
    repr: bool = ...,
    compare: bool = ...,
    iter: bool = ...,
    kw_only: bool = ...,
    serialize: bool = ...,
    exclude_field: bool = ...,
    private: bool = ...,
    doc: str | None = ...,
    metadata: dict | None = ...,
    type: type | _NothingType = ...,
) -> _T: ...

@typing.overload
def attribute(
    *,
    default: _NothingType = NOTHING,
    default_factory: _NothingType = NOTHING,
    init: bool = ...,
    repr: bool = ...,
    compare: bool = ...,
    iter: bool = ...,
    kw_only: bool = ...,
    serialize: bool = ...,
    exclude_field: bool = ...,
    private: bool = ...,
    doc: str | None = ...,
    metadata: dict | None = ...,
    type: type | _NothingType = ...,
) -> typing.Any: ...

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
    _meta_gatherer: Callable[[type | _CopiableMappings], tuple[dict[str, Field], dict[str, typing.Any]]] = ...
    __slots__: dict[str, typing.Any] = ...
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

# As far as I can tell these are the correct types
# But mypy.stubtest crashes trying to analyse them
# Due to the combination of overload and dataclass_transform
# @typing.overload
# def prefab(
#     cls: None = None,
#     *,
#     init: bool = ...,
#     repr: bool = ...,
#     eq: bool = ...,
#     iter: bool = ...,
#     match_args: bool = ...,
#     kw_only: bool = ...,
#     frozen: bool = ...,
#     dict_method: bool = ...,
#     recursive_repr: bool = ...,
# ) -> Callable[[type[_T]], type[_T]]: ...

# @dataclass_transform(field_specifiers=(Attribute, attribute))
# @typing.overload
# def prefab(
#     cls: type[_T],
#     *,
#     init: bool = ...,
#     repr: bool = ...,
#     eq: bool = ...,
#     iter: bool = ...,
#     match_args: bool = ...,
#     kw_only: bool = ...,
#     frozen: bool = ...,
#     dict_method: bool = ...,
#     recursive_repr: bool = ...,
# ) -> type[_T]: ...

# As mypy crashes, and the only difference is the return type
# just return `Any` for now to avoid the overload.
@dataclass_transform(field_specifiers=(Attribute, attribute))
def prefab(
    cls: type[_T] | None = ...,
    *,
    init: bool = ...,
    repr: bool = ...,
    eq: bool = ...,
    iter: bool = ...,
    match_args: bool = ...,
    kw_only: bool = ...,
    frozen: bool = ...,
    dict_method: bool = ...,
    recursive_repr: bool = ...,
) -> typing.Any: ...

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

def replace(obj: _T, /, **changes: typing.Any) -> _T: ...
