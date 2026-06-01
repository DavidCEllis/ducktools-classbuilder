import sys
import types
import typing
import typing_extensions

__lazy_modules__: list[str]

from collections.abc import Callable, Iterable, Mapping
from types import MappingProxyType

if sys.version_info >= (3, 14):
    import annotationlib

    _py_type = annotationlib.ForwardRef | type | str
else:
    _py_type = type | str

_CopiableMappings = dict[str, typing.Any] | MappingProxyType[str, typing.Any]

_T = typing.TypeVar("_T")
_FieldType = typing.TypeVar("_FieldType", bound=Field)
_gatherer_argtype = type | _CopiableMappings
_gatherer_returntype = tuple[dict[str, Field], dict[str, typing.Any]]

__version__: str
__version_tuple__: tuple[str | int, ...]
INTERNALS_DICT: str
META_GATHERER_NAME: str
GATHERED_DATA: str
REPLACE_NAME: str


@typing.type_check_only
class GetFieldsProtocol(typing.Protocol):
    def __call__(self, cls: type, *, local: bool = ...) -> Mapping[str, Field]: ...

def get_fields(cls: type, *, local: bool = ...) -> dict[str, Field]: ...

def get_flags(cls: type) -> dict[str, bool]: ...

def get_methods(cls: type) -> types.MappingProxyType[str, MethodMaker]: ...

def get_generated_code(cls: type) -> dict[str, GeneratedCode]: ...

def print_generated_code(cls: type) -> None: ...

def build_completed(cls: type) -> bool: ...


class _NothingType:
    custom: str | None
    def __new__(cls, custom: str | None = ...) -> typing.Self: ...
    def __repr__(self) -> str: ...
NOTHING: _NothingType
FIELD_NOTHING: _NothingType

class _KW_ONLY_META(type):
    def __repr__(self) -> str: ...

class KW_ONLY(metaclass=_KW_ONLY_META): ...

# Stub Only Protocols
@typing.type_check_only
class _CodegenType(typing.Protocol):
    def __call__(self, cls: type, funcname: str = ...) -> GeneratedCode: ...

@typing.type_check_only
class _ArgcountCodegenType(typing.Protocol):
    def __call__(self, argcount: int, funcname: str = ...) -> GeneratedCode: ...

class _CacheStats:
    __slots__: tuple[str, str]
    hits: int
    misses: int
    @property
    def hit_percent(self) -> float: ...
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...

@typing.type_check_only
class _CachedFunctionBuilder(typing.Protocol):
    def __call__(self, cls: type, funcname: str = ...) -> tuple[GeneratedCode, types.FunctionType]: ...
    def clear_cache(self, new_cache: None | dict[str, typing.Any] = ...) -> None: ...
    def get_stats(self) -> _CacheStats: ...

@typing.type_check_only
class GathererProtocol(typing.Protocol, typing.Generic[_FieldType]):
    def __call__(self, cls: _gatherer_argtype) -> tuple[dict[str, _FieldType], dict[str, typing.Any]]: ...

@typing.type_check_only
class AnnotationGathererProtocol(typing.Protocol, typing.Generic[_FieldType]):
    def __call__(
        self,
        cls: _gatherer_argtype,
        *,
        cls_annotations: None | dict[str, typing.Any]
    ) -> tuple[dict[str, _FieldType], dict[str, typing.Any]]: ...

class GeneratedCode:
    __slots__: tuple[str, ...]
    source_code: str
    globs: dict[str, typing.Any]
    annotations: dict[str, typing.Any]

    def __init__(
        self,
        source_code: str,
        globs: dict[str, typing.Any] | None = ...,
        annotations: dict[str, typing.Any] | None = ...,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def generate(self) -> types.FunctionType: ...

class MethodMaker:
    funcname: str
    code_generator: _CodegenType
    cached_generator: _CachedFunctionBuilder
    decorator: None | Callable[[types.FunctionType], types.FunctionType]
    def __init__(
        self,
        funcname: str,
        code_generator: _CodegenType,
        cached_generator: None | _CachedFunctionBuilder = ...,
        decorator: None | Callable[[types.FunctionType], types.FunctionType] = ...,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __get__(self, instance, cls) -> types.FunctionType: ...

class _SignatureMaker:
    def __get__(self, instance, cls=None) -> typing_extensions.Never: ...

signature_maker: _SignatureMaker

def get_empty_args(cls: type) -> tuple[tuple[()]]: ...
def get_compare_args(cls: type) -> tuple[tuple[str, ...]]: ...
def get_repr_args(cls: type) -> tuple[tuple[str, ...]]: ...
def get_replace_args(cls: type) -> tuple[tuple[str, ...]]: ...
def get_frozen_setattr_args(cls: type) -> tuple[tuple[()], bool]: ...

# These could be stricter
def get_empty_globals(cls: type) -> dict[str, typing.Any]: ...
def get_frozen_setattr_globals(cls: type) -> dict[str, typing.Any]: ...

def counter_to_class_generator(
    counter_generator: _ArgcountCodegenType,
    argument_getter: Callable[[type], tuple],
    globals_getter: Callable[[type], dict[str, typing.Any]] = ...,
    *,
    cache: None | dict[str, types.FunctionType] = ...,
    replace_strings: bool = ...,
) -> _CachedFunctionBuilder: ...


def get_init_generator(
    null: _NothingType = NOTHING,
    extra_code: None | list[str] = None
) -> _CodegenType: ...

def init_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

def generic_repr_generator(field_names: list[str], *, funcname: str = ...) -> GeneratedCode: ...
def class_repr_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

def generic_eq_generator(field_names: list[str], *, funcname: str = ...) -> GeneratedCode: ...
def class_eq_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

def get_generic_order_generator(field_names: list[str], operator: str, *, funcname: str) -> GeneratedCode: ...
def get_class_order_generator(cls: type, operator: str, *, funcname: str) -> GeneratedCode: ...
def class_lt_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def class_le_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def class_gt_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def class_ge_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

def generic_replace_generator(field_pairs: list[tuple[str, str]], *, funcname: str = ...) -> GeneratedCode: ...
def class_replace_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

def frozen_setattr_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

def generic_frozen_setattr_generator(slotted: bool, *, funcname: str = ...) -> GeneratedCode: ...
def generic_frozen_delattr_generator(*, funcname: str = ...) -> GeneratedCode: ...
def frozen_delattr_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

def generic_hash_generator(field_names: list[str], *, funcname: str = ...) -> GeneratedCode: ...
def hash_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

init_maker: MethodMaker
repr_maker: MethodMaker
eq_maker: MethodMaker
lt_maker: MethodMaker
le_maker: MethodMaker
gt_maker: MethodMaker
ge_maker: MethodMaker
replace_maker: MethodMaker
frozen_setattr_maker: MethodMaker
frozen_delattr_maker: MethodMaker
hash_maker: MethodMaker
default_methods: frozenset[MethodMaker]

_TypeT = typing.TypeVar("_TypeT", bound=type)

def add_methods(
    cls: type,
    methods: Iterable[MethodMaker],
    *,
    internals: None | dict[str, typing.Any] = ...
) -> dict[str, MethodMaker]: ...

@typing.overload
def builder(
    cls: _TypeT,
    /,
    *,
    gatherer: GathererProtocol[Field],
    methods: frozenset[MethodMaker] | set[MethodMaker],
    flags: dict[str, bool] | None = None,
    fix_signature: bool = ...,
    field_getter: GetFieldsProtocol = ...,
) -> _TypeT: ...

@typing.overload
def builder(
    cls: None = None,
    /,
    *,
    gatherer: GathererProtocol[Field],
    methods: frozenset[MethodMaker] | set[MethodMaker],
    flags: dict[str, bool] | None = None,
    fix_signature: bool = ...,
    field_getter: GetFieldsProtocol = ...,
) -> Callable[[_TypeT], _TypeT]: ...


class SlotFields(dict):
    ...


class SlotMakerMeta(type):
    def __new__(
        cls: type[_TypeT],
        name: str,
        bases: tuple[type, ...],
        ns: dict[str, typing.Any],
        slots: bool = ...,
        gatherer: GathererProtocol | None = ...,
        ignore_annotations: bool | None = ...,
        **kwargs: typing.Any,
    ) -> _TypeT: ...


# Only technically frozen under testing but we should *act* like they are frozen
# Field is its own field specifier
@typing.dataclass_transform(field_specifiers=(Field,), frozen_default=True)  # noqa: F821
class Field(metaclass=SlotMakerMeta):
    default: _NothingType | typing.Any
    default_factory: _NothingType | typing.Any
    type: _NothingType | _py_type
    doc: None | str
    init: bool
    repr: bool
    compare: bool
    kw_only: bool

    __slots__: dict[str, str]
    __classbuilder_internals__: dict
    __signature__: _SignatureMaker

    def __init__(
        self,
        *,
        default: _NothingType | typing.Any = ...,
        default_factory: _NothingType | typing.Any = ...,
        type: _NothingType | _py_type = ...,
        doc: None | str = ...,
        init: bool = ...,
        repr: bool = ...,
        compare: bool = ...,
        kw_only: bool = ...,
    ) -> None: ...

    def __init_subclass__(cls, frozen: bool = ..., ignore_annotations: bool = ...): ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: Field | object) -> bool: ...
    def __replace__(self, **kwargs) -> typing.Self: ...
    def validate_field(self) -> None: ...
    @classmethod
    def from_field(cls, fld: Field, /, **kwargs: typing.Any) -> typing.Self: ...

# These types only exist because type[Field] doesn't seem to resolve correctly
# Technically they're wrong as `isinstance` gets used
_ReturnsField = Callable[..., Field]

@typing.type_check_only
class NoArgGathererProtocol(typing.Protocol):
    def __call__(
        self,
        cls: _gatherer_argtype,
        *,
        cls_annotations: None | dict[str, typing.Any]
    ) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...

@typing.type_check_only
class NoArgAnnotationGathererProtocol(typing.Protocol):
    def __call__(
        self,
        cls: _gatherer_argtype,
        *,
        cls_annotations: None | dict[str, typing.Any]
    ) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...


@typing.overload
def make_slot_gatherer(
    field_type: _ReturnsField = ...,
) -> NoArgGathererProtocol: ...

@typing.overload
def make_slot_gatherer(
    field_type: type[_FieldType],
) -> GathererProtocol[_FieldType]: ...

@typing.overload
def make_annotation_gatherer(
    field_type: _ReturnsField = ...,
    leave_default_values: bool = False,
) -> NoArgAnnotationGathererProtocol: ...

@typing.overload
def make_annotation_gatherer(
    field_type: type[_FieldType],
    leave_default_values: bool = False,
) -> AnnotationGathererProtocol[_FieldType]: ...

@typing.overload
def make_field_gatherer(
    field_type: _ReturnsField = ...,
    leave_default_values: bool = False,
) -> NoArgGathererProtocol: ...

@typing.overload
def make_field_gatherer(
    field_type: type[_FieldType],
    leave_default_values: bool = False,
) -> GathererProtocol[_FieldType]: ...

@typing.overload
def make_unified_gatherer(
    field_type: _ReturnsField = ...,
    leave_default_values: bool = ...,
) -> NoArgGathererProtocol: ...

@typing.overload
def make_unified_gatherer(
    field_type: type[_FieldType],
    leave_default_values: bool = ...,
) -> GathererProtocol[_FieldType]: ...

def slot_gatherer(cls_or_ns: type | _CopiableMappings) -> _gatherer_returntype: ...
def annotation_gatherer(
    cls_or_ns: type | _CopiableMappings,
    *,
    cls_annotations: None | dict[str, typing.Any] = ...
) -> _gatherer_returntype: ...

def unified_gatherer(cls_or_ns: type | _CopiableMappings) -> _gatherer_returntype: ...


def check_argument_order(cls: type) -> None: ...

def replace(obj: _T, /, **changes: typing.Any) -> _T: ...

@typing.overload
def slotclass(
    cls: _TypeT,
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
    syntax_check: bool = True
) -> _TypeT: ...

@typing.overload
def slotclass(
    cls: None = None,
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
    syntax_check: bool = True
) -> Callable[[_TypeT], _TypeT]: ...


_gatherer_type = Callable[[type | _CopiableMappings], tuple[dict[str, Field], dict[str, typing.Any]]]

class GatheredFields:
    __slots__: tuple[str, ...]

    fields: dict[str, Field]
    modifications: dict[str, typing.Any]

    def __init__(
        self,
        fields: dict[str, Field],
        modifications: dict[str, typing.Any]
    ) -> None: ...

    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def __call__(self, cls_dict: type | dict[str, typing.Any]) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...
