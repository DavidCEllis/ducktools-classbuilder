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
import types

_CopiableMappings = dict[str, typing.Any] | types.MappingProxyType[str, typing.Any]

def get_func_annotations(
    func: types.FunctionType,
) -> dict[str, typing.Any]: ...

def get_ns_annotations(
    ns: _CopiableMappings,
    cls: type | None = ...,
) -> dict[str, typing.Any]: ...

def is_classvar(
    hint: object,
) -> bool: ...

def resolve_type(object, deferred_as_str: bool = ...) -> object: ...

def apply_annotations(obj: typing.Any, annotations: dict[str, typing.Any]) -> None: ...

def is_type(hint: str | object, t: type) -> bool: ...


if sys.version_info >= (3, 14):
    from reannotate import DeferredAnnotation
    @typing.overload
    def replace_generics_with_arg(hint: DeferredAnnotation) -> DeferredAnnotation: ...

    @typing.overload
    def replace_generics_with_arg(hint: str) -> str: ...

    @typing.overload
    def replace_generics_with_arg(hint: typing.Any) -> typing.Any: ...
else:
    @typing.overload
    def replace_generics_with_arg(hint: str) -> str: ...

    @typing.overload
    def replace_generics_with_arg(hint: typing.Any) -> typing.Any: ...
