import typing
from collections.abc import Callable

_py_type = type | str  # Alias for type hint values

__version__: str
INTERNALS_DICT: str

def get_fields(cls: type, *, local: bool = False) -> dict[str, Field]: ...

def get_flags(cls:type) -> dict[str, bool]: ...

def _get_inst_fields(inst: typing.Any) -> dict[str, typing.Any]: ...

class _NothingType:
    ...
NOTHING: _NothingType

# Stub Only
_codegen_type = Callable[[type], tuple[str, dict[str, typing.Any]]]

class MethodMaker:
    funcname: str
    code_generator: _codegen_type
    def __init__(self, funcname: str, code_generator: _codegen_type) -> None: ...
    def __repr__(self) -> str: ...
    def __get__(self, instance, cls) -> Callable: ...

def get_init_generator(
    null: _NothingType = NOTHING,
    extra_code: None | list[str] = None
) -> Callable[[type], tuple[str, dict[str, typing.Any]]]: ...

def init_generator(cls: type) -> tuple[str, dict[str, typing.Any]]: ...
def repr_generator(cls: type) -> tuple[str, dict[str, typing.Any]]: ...
def eq_generator(cls: type) -> tuple[str, dict[str, typing.Any]]: ...

def frozen_setattr_generator(cls: type) -> tuple[str, dict[str, typing.Any]]: ...

def frozen_delattr_generator(cls: type) -> tuple[str, dict[str, typing.Any]]: ...

init_maker: MethodMaker
repr_maker: MethodMaker
eq_maker: MethodMaker
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
) -> type[_T]: ...

@typing.overload
def builder(
    cls: None = None,
    /,
    *,
    gatherer: Callable[[type], tuple[dict[str, Field], dict[str, typing.Any]]],
    methods: frozenset[MethodMaker] | set[MethodMaker],
    flags: dict[str, bool] | None = None,
) -> Callable[[type[_T]], type[_T]]: ...


class Field:
    default: _NothingType | typing.Any
    default_factory: _NothingType | typing.Any
    type: _NothingType | _py_type
    doc: None | str

    __slots__: dict[str, str]
    __classbuilder_internals__: dict

    def __init__(
        self,
        *,
        default: _NothingType | typing.Any = NOTHING,
        default_factory: _NothingType | typing.Any = NOTHING,
        type: _NothingType | _py_type = NOTHING,
        doc: None | str = None,
    ) -> None: ...

    def __init_subclass__(cls, frozen: bool = False): ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: Field | object) -> bool: ...
    def validate_field(self) -> None: ...
    @classmethod
    def from_field(cls, fld: Field, /, **kwargs: typing.Any) -> Field: ...


class GatheredFields:
    __slots__ = ("fields", "modifications")

    fields: dict[str, Field]
    modifications: dict[str, typing.Any]

    __classbuilder_internals__: dict

    def __init__(
        self,
        fields: dict[str, Field],
        modifications: dict[str, typing.Any]
    ) -> None: ...

    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def __call__(self, cls: type) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...


class SlotFields(dict):
    ...

_FieldType = typing.TypeVar("_FieldType", bound=Field)

@typing.overload
def make_slot_gatherer(
    field_type: type[_FieldType]
) -> Callable[[type], tuple[dict[str, _FieldType], dict[str, typing.Any]]]: ...

@typing.overload
def make_slot_gatherer(
) -> Callable[[type], tuple[dict[str, Field], dict[str, typing.Any]]]: ...

def slot_gatherer(cls: type) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...

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
