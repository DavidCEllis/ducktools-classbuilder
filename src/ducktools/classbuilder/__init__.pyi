import typing
from collections.abc import Callable

_py_type = type  # Alias for type where it is used as a name

__version__: str
INTERNALS_DICT: str

def get_internals(cls) -> dict[str, typing.Any] | None: ...

def get_fields(cls: type) -> dict[str, Field]: ...

def get_inst_fields(inst: typing.Any) -> dict[str, typing.Any]: ...

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

def init_maker(
    cls: type,
    *,
    null: _NothingType = NOTHING,
    kw_only: bool = False
) -> tuple[str, dict[str, typing.Any]]: ...
def repr_maker(cls: type) -> tuple[str, dict[str, typing.Any]]: ...
def eq_maker(cls: type) -> tuple[str, dict[str, typing.Any]]: ...

init_desc: MethodMaker
repr_desc: MethodMaker
eq_desc: MethodMaker
default_methods: frozenset[MethodMaker]

_T = typing.TypeVar("_T")

@typing.overload
def builder(
    cls: type[_T],
    /,
    *,
    gatherer: Callable[[type], dict[str, Field]],
    methods: frozenset[MethodMaker] | set[MethodMaker]
) -> type[_T]: ...

@typing.overload
def builder(
    cls: None = None,
    /,
    *,
    gatherer: Callable[[type], dict[str, Field]],
    methods: frozenset[MethodMaker] | set[MethodMaker]
) -> Callable[[type[_T]], type[_T]]: ...


class Field:
    default: _NothingType | typing.Any
    default_factory: _NothingType | typing.Any
    type: _NothingType | _py_type
    doc: None | str

    __classbuilder_internals__: dict

    def __init__(
        self,
        *,
        default: _NothingType | typing.Any = NOTHING,
        default_factory: _NothingType | typing.Any = NOTHING,
        type: _NothingType | _py_type = NOTHING,
        doc: None | str = None,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: Field | object) -> bool: ...
    def validate_field(self) -> None: ...
    @classmethod
    def from_field(cls, fld: Field, /, **kwargs: typing.Any) -> Field: ...


class SlotFields(dict):
    ...

def slot_gatherer(cls: type) -> dict[str, Field]:
    ...

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

def fieldclass(cls: type[_T]) -> type[_T]: ...
