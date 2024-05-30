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
import builtins


class _StringGlobs(dict):
    """
    Based on the fake globals dictionary used for annotations
    from 3.14. This allows us to evaluate containers which
    include forward references.

    It's just a dictionary that returns the key if the key
    is not found.
    """
    def __missing__(self, key):
        return key

    def __repr__(self):
        cls_name = self.__class__.__name__
        dict_repr = super().__repr__()
        return f"{cls_name}({dict_repr})"


def eval_hint(hint, context=None, *, recursion_limit=5):
    """
    Attempt to evaluate a string type hint in the given
    context.

    If this raises an exception, return the last string.

    If the recursion limit is hit or a previous value returns
    on evaluation, return the original hint string.

    Example::
        import builtins
        from typing import ClassVar

        from ducktools.classbuilder.annotations import eval_hint

        foo = "foo"

        context = {**vars(builtins), **globals(), **locals()}
        eval_hint("foo", context)  # returns 'foo'

        eval_hint("ClassVar[str]", context)  # returns typing.ClassVar[str]
        eval_hint("ClassVar[forwardref]", context)  # returns typing.ClassVar[ForwardRef('forwardref')]

    :param hint: The existing type hint
    :param context: merged context
    :param recursion_limit: maximum number of evaluation loops before
                            returning the original string.
    :return: evaluated hint, or string if it could not evaluate
    """
    if context is not None:
        context = _StringGlobs(context)

    original_hint = hint
    seen = set()
    i = 0
    while isinstance(hint, str):
        seen.add(hint)

        # noinspection PyBroadException
        try:
            hint = eval(hint, context)
        except Exception:
            break

        if hint in seen or i >= recursion_limit:
            hint = original_hint
            break

        i += 1

    return hint


def get_ns_annotations(ns, eval_str=True):
    """
    Given a class namespace, attempt to retrieve the
    annotations dictionary and evaluate strings.

    Note: This only evaluates in the context of module level globals
    and values in the class namespace. Non-local variables will not
    be evaluated.

    :param ns: Class namespace (eg cls.__dict__)
    :param eval_str: Attempt to evaluate string annotations (default to True)
    :return: dictionary of evaluated annotations
    """
    raw_annotations = ns.get("__annotations__", {})

    if not eval_str:
        return raw_annotations.copy()

    try:
        obj_modulename = ns["__module__"]
    except KeyError:
        obj_module = None
    else:
        obj_module = sys.modules.get(obj_modulename, None)

    if obj_module:
        obj_globals = vars(obj_module)
    else:
        obj_globals = {}

    # Type parameters should be usable in hints without breaking
    # This is for Python 3.12+
    type_params = {
        repr(param): param
        for param in ns.get("__type_params__", ())
    }

    context = {**vars(builtins), **obj_globals, **type_params, **ns}

    return {
        k: eval_hint(v, context)
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

