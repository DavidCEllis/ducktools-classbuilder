import types
import typing
import typing_extensions

import inspect

from collections.abc import Callable
from types import MappingProxyType

_py_type = type | str  # Alias for type hint values
_CopiableMappings = dict[str, typing.Any] | MappingProxyType[str, typing.Any]

__version__: str
__version_tuple__: tuple[str | int, ...]
INTERNALS_DICT: str
META_GATHERER_NAME: str
GATHERED_DATA: str

def get_fields(cls: type, *, local: bool = False) -> dict[str, Field]: ...

def get_flags(cls: type) -> dict[str, bool]: ...

def get_methods(cls: type) -> types.MappingProxyType[str, MethodMaker]: ...

def _get_inst_fields(inst: typing.Any) -> dict[str, typing.Any]: ...

class _NothingType:
    def __init__(self, custom: str | None = ...) -> None: ...
    def __repr__(self) -> str: ...
NOTHING: _NothingType
FIELD_NOTHING: _NothingType

class _KW_ONLY_META(type):
    def __repr__(self) -> str: ...

class KW_ONLY(metaclass=_KW_ONLY_META): ...

# Stub Only
@typing.type_check_only
class _CodegenType(typing.Protocol):
    def __call__(self, cls: type, funcname: str = ...) -> GeneratedCode: ...


class GeneratedCode:
    __slots__: tuple[str, str]
    source_code: str
    globs: dict[str, typing.Any]

    def __init__(self, source_code: str, globs: dict[str, typing.Any]) -> None: ...
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
def replace_generator(cls: type, funcname: str = "__replace__") -> GeneratedCode: ...

def frozen_setattr_generator(cls: type, funcname: str = "__setattr__") -> GeneratedCode: ...

def frozen_delattr_generator(cls: type, funcname: str = "__delattr__") -> GeneratedCode: ...

init_maker: MethodMaker
repr_maker: MethodMaker
eq_maker: MethodMaker
replace_maker: MethodMaker
frozen_setattr_maker: MethodMaker
frozen_delattr_maker: MethodMaker
default_methods: frozenset[MethodMaker]

_T = typing.TypeVar("_T")

@typing.overload
def builder(
    cls: type[_T],
    /,
    *,
    gatherer: Callable[[type], tuple[dict[str, Field], dict[str, typing.Any]]],
    methods: frozenset[MethodMaker] | set[MethodMaker],
    flags: dict[str, bool] | None = None,
    fix_signature: bool = ...,
) -> type[_T]: ...

@typing.overload
def builder(
    cls: None = None,
    /,
    *,
    gatherer: Callable[[type], tuple[dict[str, Field], dict[str, typing.Any]]],
    methods: frozenset[MethodMaker] | set[MethodMaker],
    flags: dict[str, bool] | None = None,
    fix_signature: bool = ...,
) -> Callable[[type[_T]], type[_T]]: ...


class SlotFields(dict):
    ...


class SlotMakerMeta(type):
    def __new__(
        cls: type[_T],
        name: str,
        bases: tuple[type, ...],
        ns: dict[str, typing.Any],
        slots: bool = ...,
        gatherer: Callable[[type], tuple[dict[str, Field], dict[str, typing.Any]]] | None = ...,
        **kwargs: typing.Any,
    ) -> _T: ...


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
        default: _NothingType | typing.Any = NOTHING,
        default_factory: _NothingType | typing.Any = NOTHING,
        type: _NothingType | _py_type = NOTHING,
        doc: None | str = None,
        init: bool = True,
        repr: bool = True,
        compare: bool = True,
        kw_only: bool = False,
    ) -> None: ...

    def __init_subclass__(cls, frozen: bool = False): ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: Field | object) -> bool: ...
    def validate_field(self) -> None: ...
    @classmethod
    def from_field(cls, fld: Field, /, **kwargs: typing.Any) -> Field: ...


# type[Field] doesn't work due to metaclass
# This is not really precise enough because isinstance is used
_ReturnsField = Callable[..., Field]
_FieldType = typing.TypeVar("_FieldType", bound=Field)

def pre_gathered_gatherer(
    cls_or_ns: type | _CopiableMappings
) -> tuple[dict[str, Field | _FieldType], dict[str, typing.Any]]: ...

@typing.overload
def make_slot_gatherer(
    field_type: type[_FieldType]
) -> Callable[[type | _CopiableMappings], tuple[dict[str, _FieldType], dict[str, typing.Any]]]: ...

@typing.overload
def make_slot_gatherer(
    field_type: _ReturnsField = Field
) -> Callable[[type | _CopiableMappings], tuple[dict[str, Field], dict[str, typing.Any]]]: ...

@typing.overload
def make_annotation_gatherer(
    field_type: type[_FieldType],
    leave_default_values: bool = False,
) -> Callable[[type | _CopiableMappings], tuple[dict[str, _FieldType], dict[str, typing.Any]]]: ...

@typing.overload
def make_annotation_gatherer(
    field_type: _ReturnsField = Field,
    leave_default_values: bool = False,
) -> Callable[[type | _CopiableMappings], tuple[dict[str, Field], dict[str, typing.Any]]]: ...

@typing.overload
def make_field_gatherer(
    field_type: type[_FieldType],
    leave_default_values: bool = False,
    assign_types: bool = True,
) -> Callable[[type | _CopiableMappings], tuple[dict[str, _FieldType], dict[str, typing.Any]]]: ...

@typing.overload
def make_field_gatherer(
    field_type: _ReturnsField = Field,
    leave_default_values: bool = False,
) -> Callable[[type | _CopiableMappings], tuple[dict[str, Field], dict[str, typing.Any]]]: ...

@typing.overload
def make_unified_gatherer(
    field_type: type[_FieldType],
    leave_default_values: bool = ...,
    ignore_annotations: bool = ...,
) -> Callable[[type | _CopiableMappings], tuple[dict[str, _FieldType], dict[str, typing.Any]]]: ...

@typing.overload
def make_unified_gatherer(
    field_type: _ReturnsField = ...,
    leave_default_values: bool = ...,
    ignore_annotations: bool = ...,
) -> Callable[[type | _CopiableMappings], tuple[dict[str, Field], dict[str, typing.Any]]]: ...


def slot_gatherer(cls_or_ns: type | _CopiableMappings) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...
def annotation_gatherer(cls_or_ns: type | _CopiableMappings) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...

def unified_gatherer(cls_or_ns: type | _CopiableMappings) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...


def check_argument_order(cls: type) -> None: ...

@typing.overload
def slotclass(
    cls: type[_T],
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
    syntax_check: bool = True
) -> type[_T]: ...

@typing.overload
def slotclass(
    cls: None = None,
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
    syntax_check: bool = True
) -> Callable[[type[_T]], type[_T]]: ...


_gatherer_type = Callable[[type | _CopiableMappings], tuple[dict[str, Field], dict[str, typing.Any]]]

class GatheredFields:
    __slots__: tuple[str, ...]

    fields: dict[str, Field]
    modifications: dict[str, typing.Any]

    __classbuilder_internals__: dict
    __signature__: inspect.Signature

    def __init__(
        self,
        fields: dict[str, Field],
        modifications: dict[str, typing.Any]
    ) -> None: ...

    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def __call__(self, cls_dict: type | dict[str, typing.Any]) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...
