# MIT License
#
# Copyright (c) 2024 David C Ellis
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


def eval_hint(hint, obj_globals=None, obj_locals=None):
    """
    Attempt to evaluate a string type hint in the given
    context. If this fails, return the original string.

    :param hint: The existing type hint
    :param obj_globals: global context
    :param obj_locals: local context
    :return: evaluated hint, or string if it could not evaluate
    """
    while isinstance(hint, str):
        # noinspection PyBroadException
        try:
            hint = eval(hint, obj_globals, obj_locals)
        except Exception:
            break
    return hint


def get_annotations(ns, eval_str=True):
    """
    Given an class namespace, attempt to retrieve the
    annotations dictionary and evaluate strings.

    :param ns: Class namespace (eg cls.__dict__)
    :param eval_str: Attempt to evaluate string annotations (default to True)
    :return: dictionary of evaluated annotations
    """
    raw_annotations = ns.get("__annotations__", {})

    if not eval_str:
        return raw_annotations

    try:
        obj_modulename = ns["__module__"]
    except KeyError:
        obj_module = None
    else:
        obj_module = sys.modules.get(obj_modulename, None)

    if obj_module:
        obj_globals = obj_module.__dict__.copy()
    else:
        obj_globals = {}

    obj_locals = ns.copy()

    return {
        k: eval_hint(v, obj_globals, obj_locals)
        for k, v in raw_annotations.items()
    }


def is_classvar(hint):
    _typing = sys.modules.get("typing")
    if _typing:
        # Annotated is a nightmare I'm never waking up from
        # 3.8 and 3.9 need Annotated from typing_extensions
        # 3.8 also needs get_origin from typing_extensions
        if sys.version_info < (3, 10):
            _typing_extensions = sys.modules.get("typing_extensions")
            if _typing_extensions:
                _Annotated = _typing_extensions.Annotated
                _get_origin = _typing_extensions.get_origin
            else:
                _Annotated, _get_origin = None, None
        else:
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

