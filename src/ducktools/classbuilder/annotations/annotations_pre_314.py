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


def get_func_annotations(func):
    """
    Given a function, return the annotations dictionary

    :param func: function object
    :return: dictionary of annotations
    """
    return func.__annotations__


# This is simplified under 3.13 or earlier
def get_ns_annotations(ns, cls=None):
    annotations = ns.get("__annotations__")
    if annotations is not None:
        annotations = annotations.copy()
    else:
        annotations = {}
    return annotations


def resolve_type(obj, stringify_forwardrefs=False):
    return obj


def apply_annotations(obj, annotations):
    obj.__annotations__ = annotations


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
