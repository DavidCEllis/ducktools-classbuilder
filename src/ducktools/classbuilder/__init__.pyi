# MIT License
#
# Copyright (c) 2024-2026 David C Ellis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import typing

__lazy_modules__: list[str]

from collections.abc import Callable, Mapping
from types import MappingProxyType

from .constants import _NothingType
from .methods import MethodMaker

if sys.version_info >= (3, 14):
    import reannotate
    import annotationlib

    type _private_type = reannotate.DeferredAnnotation | type | str
    type _field_type = annotationlib.ForwardRef | type | str
else:
    type _private_type = type | str
    type _field_type =  type | str

type _CopiableMappings = dict[str, typing.Any] | MappingProxyType[str, typing.Any]

type _gatherer_argtype = type | _CopiableMappings
type _gatherer_returntype = tuple[dict[str, Field], dict[str, typing.Any]]

__version__: str
__version_tuple__: tuple[str | int, ...]


@typing.type_check_only
class GetFieldsProtocol(typing.Protocol):
    def __call__(self, cls: type, *, local: bool = ...) -> Mapping[str, Field]: ...


@typing.type_check_only
class NoArgGathererProtocol(typing.Protocol):
    def __call__(
        self,
        cls_or_ns: _gatherer_argtype,
        *,
        cls_annotations: None | dict[str, typing.Any]
    ) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...

@typing.type_check_only
class NoArgAnnotationGathererProtocol(typing.Protocol):
    def __call__(
        self, cls_or_ns: _gatherer_argtype, *, cls_annotations: None | dict[str, typing.Any]
    ) -> tuple[dict[str, Field], dict[str, typing.Any]]: ...

@typing.type_check_only
class GathererProtocol[FT: Field](typing.Protocol):
    def __call__(
        self,
        cls_or_ns: _gatherer_argtype,
    ) -> tuple[dict[str, FT], dict[str, typing.Any]]: ...

@typing.type_check_only
class AnnotationGathererProtocol[FT: Field](typing.Protocol):
    def __call__(
        self,
        cls_or_ns: _gatherer_argtype,
        *,
        cls_annotations: None | dict[str, typing.Any],
    ) -> tuple[dict[str, FT], dict[str, typing.Any]]: ...


default_methods: frozenset[MethodMaker]

# _TypeT = typing.TypeVar("_TypeT", bound=type)

# Construction functions
@typing.overload
def builder[TypeT: type](
    cls: TypeT,
    /,
    *,
    gatherer: GathererProtocol[Field] | NoArgGathererProtocol,
    methods: frozenset[MethodMaker] | set[MethodMaker],
    flags: dict[str, bool] | None = None,
    field_getter: GetFieldsProtocol = ...,
) -> TypeT: ...
@typing.overload
def builder[TypeT: type](
    cls: None = None,
    /,
    *,
    gatherer: GathererProtocol[Field] | NoArgGathererProtocol,
    methods: frozenset[MethodMaker] | set[MethodMaker],
    flags: dict[str, bool] | None = None,
    field_getter: GetFieldsProtocol = ...,
) -> Callable[[TypeT], TypeT]: ...

class SlotFields(dict): ...

class SlotMakerMeta[TypeT: type](type):
    def __new__(
        cls: type[TypeT],
        name: str,
        bases: tuple[type, ...],
        ns: dict[str, typing.Any],
        slots: bool = ...,
        gatherer: GathererProtocol | None = ...,
        ignore_annotations: bool | None = ...,
        **kwargs: typing.Any,
    ) -> TypeT: ...

class GatheredFields:
    __slots__: tuple[str, ...] = ...

    fields: dict[str, Field]
    modifications: dict[str, typing.Any]

    def __init__(
        self, fields: dict[str, Field], modifications: dict[str, typing.Any]
    ) -> None: ...
    def __eq__(self, other) -> bool: ...
    def __call__(
        self, cls_or_ns: _gatherer_argtype,
    ) -> _gatherer_returntype: ...

# Only technically frozen under testing but we should *act* like they are frozen
# Field is its own field specifier
@typing.dataclass_transform(field_specifiers=(Field,), frozen_default=True)  # noqa: F821
class Field(metaclass=SlotMakerMeta):
    default: _NothingType | typing.Any
    default_factory: _NothingType | typing.Any
    _type: _NothingType | _private_type
    doc: None | str
    init: bool
    repr: bool
    compare: bool
    kw_only: bool

    __slots__: typing.ClassVar[dict[str, str]] = ...
    __classbuilder_internals__: dict

    def __init__(
        self,
        *,
        default: _NothingType | typing.Any = ...,
        default_factory: _NothingType | typing.Any = ...,
        type: _NothingType | _private_type = ...,
        doc: None | str = ...,
        init: bool = ...,
        repr: bool = ...,
        compare: bool = ...,
        kw_only: bool = ...,
    ) -> None: ...
    def __init_subclass__(cls, frozen: bool = ..., ignore_annotations: bool = ...): ...
    def __eq__(self, other: Field | object) -> bool: ...
    def __replace__(self, **kwargs) -> typing.Self: ...
    def validate_field(self) -> None: ...
    @classmethod
    def from_field(cls, fld: Field, /, **kwargs: typing.Any) -> typing.Self: ...
    @property
    def type(self) -> _NothingType | _field_type: ...


# These types only exist because type[Field] doesn't seem to resolve correctly
# Technically they're wrong as `isinstance` gets used

# Gatherers
def make_slot_gatherer(
    field_type: type[Field] = ...,
) -> GathererProtocol[Field]: ...

def make_annotation_gatherer(
    field_type: type[Field] = ...,
    leave_default_values: bool = False,
) -> AnnotationGathererProtocol[Field]: ...

def make_field_gatherer(
    field_type: type[Field] = ...,
    leave_default_values: bool = False,
) -> GathererProtocol[Field]: ...

def make_unified_gatherer(
    field_type: type[Field] = ...,
    leave_default_values: bool = ...,
) -> GathererProtocol[Field]: ...

def slot_gatherer(cls_or_ns: type | _CopiableMappings) -> _gatherer_returntype: ...
def annotation_gatherer(
    cls_or_ns: type | _CopiableMappings,
    *,
    cls_annotations: None | dict[str, typing.Any] = ...,
) -> _gatherer_returntype: ...
def unified_gatherer(cls_or_ns: type | _CopiableMappings) -> _gatherer_returntype: ...
def check_argument_order(cls: type) -> None: ...

# Generic replace function
def replace[T](obj: T, /, **changes: typing.Any) -> T: ...

# Basic slotclass example
@typing.overload
def slotclass[TypeT: type](
    cls: TypeT,
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
    syntax_check: bool = True,
) -> TypeT: ...
@typing.overload
def slotclass[TypeT: type](
    cls: None = None,
    /,
    *,
    methods: frozenset[MethodMaker] | set[MethodMaker] = default_methods,
    syntax_check: bool = True,
) -> Callable[[TypeT], TypeT]: ...
