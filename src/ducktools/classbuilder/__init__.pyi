import typing
from collections.abc import Callable

__version__: str
INTERNALS_DICT: str

def get_fields(cls: type) -> dict[str, Field]: ...

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

def builder(
    cls: type,
    /,
    *,
    gatherer: Callable[[type], dict[str, Field]],
    methods: frozenset[MethodMaker],
    default_check: bool = True,
) -> type: ...


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
    def __eq__(self, other: Field) -> bool: ...
    @typing.overload
    def __eq__(self, other: object) -> NotImplemented: ...


class SlotFields(dict):
    ...

def slot_gatherer(cls: type) -> dict[str, Field]:
    ...

def slotclass(
    cls: type | None = None,
    /,
    *,
    methods: frozenset[MethodMaker] = default_methods,
    default_check: bool = True
) -> type: ...

def fieldclass(cls: type) -> type: ...
