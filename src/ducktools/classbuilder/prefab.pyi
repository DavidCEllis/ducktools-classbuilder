import typing
from collections.abc import Callable

from . import (
    INTERNALS_DICT, NOTHING,
    Field, MethodMaker, SlotFields,
    builder, fieldclass, get_fields, get_internals, slot_gatherer
)

PREFAB_FIELDS: str
PREFAB_INIT_FUNC: str
PRE_INIT_FUNC: str
POST_INIT_FUNC: str

class _KW_ONLY_TYPE:
    def __repr__(self) -> str: ...

KW_ONLY: _KW_ONLY_TYPE

class PrefabError(Exception): ...

def _is_classvar(hint: type | str) -> bool: ...

def get_init_maker(*, init_name: str="__init__") -> MethodMaker: ...

def get_repr_maker(*, recursion_safe: bool = False) -> MethodMaker: ...

def get_eq_maker() -> MethodMaker: ...

def get_iter_maker() -> MethodMaker: ...

def get_frozen_setattr_maker() -> MethodMaker: ...

def get_frozen_delattr_maker() -> MethodMaker: ...

def get_asdict_maker() -> MethodMaker: ...


init_desc: MethodMaker
prefab_init_desc: MethodMaker
repr_desc: MethodMaker
recursive_repr_desc: MethodMaker
eq_desc: MethodMaker
iter_desc: MethodMaker
frozen_setattr_desc: MethodMaker
frozen_delattr_desc: MethodMaker
asdict_desc: MethodMaker

class Attribute(Field):
    __slots__: dict

    init: bool
    repr: bool
    compare: bool
    kw_only: bool
    in_dict: bool
    exclude_field: bool

    def __init__(
        self,
        *,
        default: typing.Any | NOTHING =NOTHING,
        default_factory: typing.Any | NOTHING = NOTHING,
        type: type | NOTHING = NOTHING,
        doc: str | None = None,
        init: bool = True,
        repr: bool = True,
        compare: bool = True,
        kw_only: bool = False,
        in_dict: bool = True,
        exclude_field: bool = False,
    ) -> None: ...

    def __repr__(self) -> str: ...
    @typing.overload
    def __eq__(self, other: Attribute) -> bool: ...
    def __eq__(self, other: object) -> NotImplemented: ...

    def validate_field(self) -> None: ...

def attribute(
    *,
    default: typing.Any | NOTHING = NOTHING,
    default_factory: typing.Any | NOTHING = NOTHING,
    type: type | NOTHING = NOTHING,
    doc: str | None = None,
    init: bool = True,
    repr: bool = True,
    compare: bool = True,
    kw_only: bool = False,
    in_dict: bool = True,
    exclude_field: bool = False,
) -> Attribute: ...

def attribute_gatherer(cls: type) -> dict[str, Attribute]: ...

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
) -> type: ...

@typing.dataclass_transform
def prefab(
    cls: type | None = None,
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
) -> type | Callable[[type], type]: ...

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
) -> type: ...

def is_prefab(o: typing.Any) -> bool: ...

def is_prefab_instance(o: object) -> bool: ...

def as_dict(o) -> dict[str, typing.Any]: ...
