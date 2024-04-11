import typing
from collections.abc import Callable

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

def init_maker(cls: type) -> tuple[str, dict[str, typing.Any]]: ...
def repr_maker(cls: type) -> tuple[str, dict[str, typing.Any]]: ...
def eq_maker(cls: type) -> tuple[str, dict[str, typing.Any]]: ...

init_desc: MethodMaker
repr_desc: MethodMaker
eq_desc: MethodMaker
default_methods: frozenset[MethodMaker]

@typing.overload
def builder(
    cls: type,
    /,
    *,
    gatherer: Callable[[type], dict[str, Field]],
    methods: frozenset[MethodMaker] | set[MethodMaker]
) -> typing.Any: ...

@typing.overload
def builder(
    cls: None = None,
    /,
    *,
    gatherer: Callable[[type], dict[str, Field]],
    methods: frozenset[MethodMaker] | set[MethodMaker]
) -> Callable[[type], type]: ...


_Self = typing.TypeVar("_Self", bound="Field")

class Field:
    default: _NothingType | typing.Any
    default_factory: _NothingType | typing.Any
    type: _NothingType | type
    doc: None | str

    def __init__(
        self,
        *,
        default: _NothingType | typing.Any = NOTHING,
        default_factory: _NothingType | typing.Any = NOTHING,
        type: _NothingType | type = NOTHING,
        doc: None | str = None,
    ) -> None: ...
    @property
    def _inherited_slots(self) -> list[str]: ...
    def __repr__(self) -> str: ...
    @typing.overload
    def __eq__(self, other: _Self) -> bool: ...
    @typing.overload
    def __eq__(self, other: object) -> NotImplemented: ...
    def validate_field(self) -> None: ...
    @classmethod
    def from_field(cls, fld: Field) -> _Self: ...


class SlotFields(dict):
    ...

def slot_gatherer(cls: type) -> dict[str, Field]:
    ...

@typing.overload
def slotclass(
    cls: type,
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
    syntax_check: bool = True
) -> typing.Any: ...

def slotclass(
    cls: None = None,
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
    syntax_check: bool = True
) -> Callable[[type], type]: ...

def fieldclass(cls: type) -> typing.Any: ...
