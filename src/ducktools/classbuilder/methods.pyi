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

__lazy_modules__: list[str]

import _thread
import types
import typing

from collections.abc import Callable, Iterable

from .constants import _NothingType


# Stub Only Protocols
@typing.type_check_only
class _CodegenType(typing.Protocol):
    def __call__(self, cls: type, funcname: str = ...) -> GeneratedCode: ...

@typing.type_check_only
class _InitArgcountCodegenType(typing.Protocol):
    def __call__(
        self,
        argcount: int,
        frozen: bool,
        frozen_and_slotted: bool,
        /,
        *,
        funcname: str = ...
) -> GeneratedCode: ...

@typing.type_check_only
class _SetattrArgcountCodegenType(typing.Protocol):
    def __call__(
        self,
        argcount: int,
        slotted: bool,
        /,
        *,
        funcname: str = ...
    ) -> GeneratedCode: ...

@typing.type_check_only
class _BaseArgcountCodegenType(typing.Protocol):
    def __call__(
        self,
        argcount: int,
        /,
        *,
        funcname: str = ...
    ) -> GeneratedCode: ...

type _ArgcountCodegenType = _InitArgcountCodegenType | _SetattrArgcountCodegenType | _BaseArgcountCodegenType


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
    __slots__: tuple[str, ...]
    funcname: str
    code_generator: _CodegenType
    cached_generator: _CachedFunctionBuilder
    decorator: None | Callable[[types.FunctionType], types.FunctionType]
    def __init__(
        self,
        funcname: str,
        code_generator: _CodegenType,
        *,
        cached_generator: None | _CachedFunctionBuilder = ...,
        decorator: None | Callable[[types.FunctionType], types.FunctionType] = ...,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def attach(self, cls: type) -> None: ...
    def generate(self, cls: type) -> types.FunctionType: ...

class _AttachedMethod:
    __slots__: tuple[str, ...]
    maker: MethodMaker
    cls: type

    _generated_method: types.FunctionType
    _lock: _thread.LockType

    def __init__(
        self,
        maker: MethodMaker,
        cls: type,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
    def generate(self) -> types.FunctionType: ...
    def __call__(self, *args, **kwargs) -> typing.Any: ...
    @typing.overload
    def __get__[T](
        self,
        instance: None,
        type: type[T],
    ) -> types.FunctionType: ...
    @typing.overload
    def __get__[T](
        self,
        instance: T,
        type: type[T] | None = ...,
    ) -> types.MethodType: ...

# Args
def get_empty_args(cls: type) -> tuple[tuple[()]]: ...
def get_init_args(cls: type) -> tuple[tuple[str, ...], bool, bool] | None: ...
def get_compare_args(cls: type) -> tuple[tuple[str, ...]]: ...
def get_repr_args(cls: type) -> tuple[tuple[str, ...]]: ...
def get_replace_args(cls: type) -> tuple[tuple[str, ...]]: ...
def get_frozen_setattr_args(cls: type) -> tuple[tuple[()], bool]: ...

# Globals
def get_init_globals(cls: type) -> dict[str, typing.Any]: ...
def get_frozen_setattr_globals(cls: type) -> dict[str, typing.Any]: ...

# Parameters
type _FunctionParameterType = tuple[
    tuple[str],
    int,
    int,
    tuple[typing.Any],
    dict[str, typing.Any],
    dict[str, typing.Any],
]

def get_init_parameters(cls: type) -> _FunctionParameterType: ...

# field names
def get_counter_field_names(argcount: int) -> list[str]: ...

class _CacheStats:
    __slots__: tuple[str, ...]
    hits: int
    misses: int
    skips: int

    _hitlock: _thread.LockType
    _misslock: _thread.LockType
    _skiplock: _thread.LockType

    def add_hit(self) -> None: ...
    def add_miss(self) -> None: ...
    def add_skip(self) -> None: ...

    @property
    def hit_percent(self) -> float: ...
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...

class _SimpleCache:
    __slots__: tuple[str, ...]
    _func: Callable[..., types.FunctionType]
    _internal_cache: dict[tuple, types.FunctionType]
    _stats: _CacheStats
    _lock_cache: dict[tuple, _thread.LockType]
    def __init__(
        self,
        func: types.FunctionType,
        *,
        cache_seed: dict[tuple, types.FunctionType] | None = ...,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def clear(
        self,
        new_cache: dict[tuple, types.FunctionType] | None = ...,
    ) -> None: ...
    @property
    def stats(self) -> _CacheStats: ...
    @property
    def state(self) -> types.MappingProxyType[tuple, types.FunctionType]: ...
    def __call__(self, *args, **kwargs) -> types.FunctionType: ...

def _simple_cache(
    *,
    cache_seed: dict[tuple, types.FunctionType],
) -> Callable[[types.FunctionType], _SimpleCache]: ...

@typing.type_check_only
class _CachedFunctionBuilder(typing.Protocol):
    cache: _SimpleCache
    def __call__(self, cls: type, funcname: str) -> types.FunctionType | None: ...

def counter_to_class_generator(
    counter_generator: _ArgcountCodegenType,
    argument_getter: Callable[[type], tuple | None],
    globals_getter: Callable[[type], dict[str, typing.Any]] | None = ...,
    *,
    cache: None | dict[tuple, types.FunctionType] = ...,
    replace_strings: bool = ...,
    param_updater: None | Callable[[type], _FunctionParameterType] = ...,
) -> _CachedFunctionBuilder: ...

# Actual generators
# __init__
def get_init_generator(
    null: _NothingType = ..., extra_code: None | list[str] = None
) -> _CodegenType: ...
def class_init_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def generic_init_generator(
    field_names: list[str], frozen: bool, frozen_and_slotted: bool, *, funcname: str = ...
) -> GeneratedCode: ...
def _counter_init_generator(
    argcount: int, frozen: bool, frozen_and_slotted: bool, /, *, funcname: str = ...
) -> GeneratedCode: ...

# __repr__
def generic_repr_generator(
    field_names: list[str], *, funcname: str = ...
) -> GeneratedCode: ...
def class_repr_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

# __eq__
def generic_eq_generator(
    field_names: list[str], *, funcname: str = ...
) -> GeneratedCode: ...
def class_eq_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

# __ge__, __gt__, __le__, __lt__
def get_generic_order_generator(
    field_names: list[str], operator: str, *, funcname: str
) -> GeneratedCode: ...
def get_class_order_generator(
    cls: type, operator: str, *, funcname: str
) -> GeneratedCode: ...
def class_lt_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def class_le_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def class_gt_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def class_ge_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

# __replace__
def generic_replace_generator(
    field_pairs: list[tuple[str, str]], *, funcname: str = ...
) -> GeneratedCode: ...
def class_replace_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

# __setattr__ and __delattr__
def generic_frozen_setattr_generator(
    slotted: bool, *, funcname: str = ...
) -> GeneratedCode: ...
def class_frozen_setattr_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...
def generic_frozen_delattr_generator(*, funcname: str = ...) -> GeneratedCode: ...
def class_frozen_delattr_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

# __hash__
def generic_hash_generator(
    field_names: list[str], *, funcname: str = ...
) -> GeneratedCode: ...
def class_hash_generator(cls: type, funcname: str = ...) -> GeneratedCode: ...

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

def add_methods(
    cls: type,
    methods: Iterable[MethodMaker],
    *,
    internals: None | dict[str, typing.Any] = ...,
) -> dict[str, MethodMaker]: ...
