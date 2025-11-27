import sys
import types
import typing
import typing_extensions


from collections.abc import Callable
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

@typing.type_check_only
class GetFieldsProtocol(typing.Protocol):
    def __call__(self, cls: type, *, local: bool = ...) -> dict[str, Field]: ...

def get_fields(cls: type, *, local: bool = ...) -> dict[str, Field]: ...

def get_flags(cls: type) -> dict[str, bool]: ...

def get_methods(cls: type) -> types.MappingProxyType[str, MethodMaker]: ...

def get_generated_code(cls: type) -> dict[str, GeneratedCode]: ...

def print_generated_code(cls: type) -> None: ...

def build_completed(ns: _CopiableMappings) -> bool: ...

def _get_inst_fields(inst: typing.Any) -> dict[str, typing.Any]: ...

class _NothingType:
    def __init__(self, custom: str | None = ...) -> None: ...
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
        globs: dict[str, typing.Any],
        annotations: dict[str, typing.Any] | None = ...,
    ) -> None: ...
    def __repr__(self) -> str: ...

class MethodMaker:
    funcname: str
    code_generator: _CodegenType
    def __init__(self, funcname: str, code_generator: _CodegenType) -> None: ...
    def __repr__(self) -> str: ...
    def __get__(self, instance, cls) -> Callable: ...

class _SignatureMaker:
    def __get__(self, instance, cls=None) -> typing_extensions.Never: ...

signature_maker: _SignatureMaker

def get_init_generator(
    null: _NothingType = NOTHING,
    extra_code: None | list[str] = None
) -> _CodegenType: ...

def init_generator(cls: type, funcname: str="__init__") -> GeneratedCode: ...

def get_repr_generator(
    recursion_safe: bool = False,
    eval_safe: bool = False
) -> _CodegenType: ...
def repr_generator(cls: type, funcname: str = "__repr__") -> GeneratedCode: ...
def eq_generator(cls: type, funcname: str = "__eq__") -> GeneratedCode: ...

def get_order_generator(cls: type, funcname: str, operator: str) -> GeneratedCode: ...
def lt_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def le_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def gt_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def ge_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

def replace_generator(cls: type, funcname: str = "__replace__") -> GeneratedCode: ...

def frozen_setattr_generator(cls: type, funcname: str = "__setattr__") -> GeneratedCode: ...

def frozen_delattr_generator(cls: type, funcname: str = "__delattr__") -> GeneratedCode: ...

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
default_methods: frozenset[MethodMaker]

_TypeT = typing.TypeVar("_TypeT", bound=type)

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
    def validate_field(self) -> None: ...
    @classmethod
    def from_field(cls, fld: Field, /, **kwargs: typing.Any) -> Field: ...

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
