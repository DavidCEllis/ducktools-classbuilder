import typing
from types import GenericAlias, MappingProxyType
from typing_extensions import dataclass_transform

__lazy_modules__: list[str]

# Suppress weird pylance error
from collections.abc import Callable  # type: ignore

from . import (
    NOTHING,
    Field,
    GathererProtocol,
    GeneratedCode,
    MethodMaker,
    SlotMakerMeta,
    _SignatureMaker
)

from . import (
    KW_ONLY as KW_ONLY,
    SlotFields as SlotFields,
    replace as replace,
)

# noinspection PyUnresolvedReferences
from . import _NothingType

_T = typing.TypeVar("_T")

PREFAB_FIELDS: str
PREFAB_INIT_FUNC: str
PRE_INIT_FUNC: str
POST_INIT_FUNC: str

LITERAL_TYPES: frozenset[type]
LITERAL_CONTAINERS: frozenset[type]

_CopiableMappings = dict[str, typing.Any] | MappingProxyType[str, typing.Any]

class PrefabError(Exception): ...

class InitParam(typing.Any):
    def __class_getitem__(cls, t: _T) -> GenericAlias: ...
    def __new__(cls, arg: _T) -> _T: ...  # type: ignore

def get_attributes(cls: type, *, local: bool = ...) -> dict[str, Attribute]: ...

def init_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def iter_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def as_dict_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

init_maker: MethodMaker
prefab_init_maker: MethodMaker
repr_maker: MethodMaker
eq_maker: MethodMaker
iter_maker: MethodMaker
asdict_maker: MethodMaker

class Attribute(Field):
    __slots__: dict
    __signature__: _SignatureMaker
    __classbuilder_gathered_fields__: tuple[dict[str, Field], dict[str, typing.Any]]
    __classbuilder_meta_gatherer__: GathererProtocol

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
    default: _NothingType = ...,
    default_factory: _NothingType = ...,
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
    init: bool = ...,
    repr: bool = ...,
    eq: bool = ...,
    order: bool = ...,
    iter: bool = ...,
    match_args: bool = ...,
    kw_only: bool = ...,
    frozen: bool = ...,
    replace: bool = ...,
    dict_method: bool = ...,
    gatherer: GathererProtocol[Attribute] = ...,
    gathered_fields: Callable[[type], tuple[dict[str, Attribute], dict[str, typing.Any]]] | None = ...,
    ignore_annotations: bool = ...,
) -> type: ...

# noinspection PyUnresolvedReferences
@dataclass_transform(field_specifiers=(Attribute, attribute))
class Prefab(metaclass=SlotMakerMeta):
    __classbuilder_internals__: dict[str, typing.Any]
    __classbuilder_meta_gatherer__: GathererProtocol
    __slots__: dict[str, typing.Any] = ...
    def __init_subclass__(
        cls,
        *,
        init: bool = ...,
        repr: bool = ...,
        eq: bool = ...,
        order: bool = ...,
        iter: bool = ...,
        match_args: bool = ...,
        kw_only: bool = ...,
        frozen: bool = ...,
        replace: bool = ...,
        dict_method: bool = ...,
        gatherer: GathererProtocol[Attribute] = ...,
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
    order: bool = ...,
    iter: bool = ...,
    match_args: bool = ...,
    kw_only: bool = ...,
    frozen: bool = ...,
    replace: bool = ...,
    dict_method: bool = ...,
    gatherer: GathererProtocol[Attribute] = ...,
    ignore_annotations: bool = ...,
) -> typing.Any: ...

def build_prefab(
    class_name: str,
    attributes: list[tuple[str, Attribute]],
    *,
    bases: tuple[type, ...] = (),
    class_dict: dict[str, typing.Any] | None = ...,
    init: bool = ...,
    repr: bool = ...,
    eq: bool = ...,
    order: bool = ...,
    iter: bool = ...,
    match_args: bool = ...,
    kw_only: bool = ...,
    frozen: bool = ...,
    replace: bool = ...,
    dict_method: bool = ...,
    slots: bool = ...,
) -> type: ...

def is_prefab(o: typing.Any) -> bool: ...

def is_prefab_instance(o: object) -> bool: ...

def as_dict(o) -> dict[str, typing.Any]: ...
