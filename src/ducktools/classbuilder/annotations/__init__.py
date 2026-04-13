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

if sys.version_info >= (3, 14):  # cover-req-le3.14
    from .annotations_314 import (
        apply_annotations,
        get_func_annotations,
        get_ns_annotations,
        resolve_type,
    )
else:  # cover-req-lt3.14
    from .annotations_pre_314 import (
        apply_annotations,
        get_func_annotations,
        get_ns_annotations,
        resolve_type,
    )


__all__ = [
    "apply_annotations",
    "get_func_annotations",
    "get_ns_annotations",
    "is_classvar",
    "is_type",
    "resolve_type",
]


def is_classvar(hint):
    # This is a duplicate of `is_type` but for ClassVar to avoid
    # importing ClassVar to check it
    if isinstance(hint, str):
        # String annotations, just check if the string 'ClassVar' is in there
        # This is overly broad and could be smarter.
        return "ClassVar" in hint
    else:
        _typing = sys.modules.get("typing")
        if _typing:
            _Annotated = _typing.Annotated
            _get_origin = _typing.get_origin

            if _Annotated and _get_origin(hint) is _Annotated:
                hint = getattr(hint, "__origin__", None)

            if (
                hint is _typing.ClassVar
                or getattr(hint, "__origin__", None) is _typing.ClassVar
            ):
                return True
    return False


def is_type(hint, t):
    # Resolve types as forward references
    hint = resolve_type(hint)

    if isinstance(hint, str):
        # String annotations, just check if the string name of the type
        # is in there. his is overly broad and could be smarter.
        type_str = t.__name__
        return type_str in hint

    _typing = sys.modules.get("typing")
    if _typing:
        _Annotated = _typing.Annotated
        _get_origin = _typing.get_origin

        # Strip `Annotated`
        if _get_origin(hint) is _Annotated:
            hint = hint.__origin__

    if hint is t or getattr(hint, "__origin__", None) is t:
        return True

    return False


def replace_generic_with_arg(hint):
    """
    Replace a generic type with its first argument

    EG: InitVar[str] -> str

    :param hint: Type annotation
    :return: The annotation with the generic replaced by its first
             argument
    """
    if isinstance(hint, str):
        r = hint.partition("[")[2]
        l = r.rpartition("]")[0]
        if l:
            return l.split(",")[0].strip()
        else:
            return hint

    if getattr(hint, "__origin__", None) and (args := getattr(hint, "__args__", None)):
        return args[0]

    return hint
