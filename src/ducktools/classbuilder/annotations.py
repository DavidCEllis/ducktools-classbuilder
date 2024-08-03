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


# Evil stuff from types.py
def _cell_factory():
    a = 1

    def f():
        nonlocal a
    return f.__closure__[0]
_FunctionType = type(_cell_factory)
_CellType = type(_cell_factory())
del _cell_factory
# End evil stuff from types.py


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


def eval_hint(hint, context=None, *, recursion_limit=2):
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

    # Using a set would require the hint always be hashable
    # This is only going to be 2 items at most usually
    seen = []
    i = 0
    while isinstance(hint, str):
        seen.append(hint)

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


def call_annotate_func(annotate):
    # Python 3.14 breaks the old methods of getting annotations
    # The new annotationlib currently relies on 'ast' and 'functools'
    # that this project tries to avoid importing.

    # The basic logic is copied from there, however, replacing ForwardRef
    # with a more basic class.
    # While `annotationlib` is trying to return ForwardRef objects that can
    # be evaluated later, this module only cares about annotations that can
    # be evaluated at the point this function is called.
    # As such we throw away the other information and just return strings
    # instead of forwardrefs.

    try:
        raw_annotations = annotate(1)
    except NameError:
        pass
    else:
        return raw_annotations

    # The annotate func may support forwardref natively
    try:
        raw_annotations = annotate(2)
    except NotImplementedError:
        pass
    else:
        return raw_annotations

    # Not supported so we have to implement our own deferred handling
    # Some modified logic from annotationlib
    namespace = {**annotate.__builtins__, **annotate.__globals__}
    globs = _StringGlobs(namespace)

    # This handles closures where the variable is defined after get annotations is called.
    if annotate.__closure__:
        freevars = annotate.__code__.co_freevars
        new_closure = []
        for i, cell in enumerate(annotate.__closure__):
            try:
                cell.cell_contents
            except ValueError:
                if i < len(freevars):
                    name = freevars[i]
                else:
                    name = "__cell__"
                new_closure.append(_CellType(name))
            else:
                new_closure.append(cell)
        closure = tuple(new_closure)
    else:
        closure = None

    new_annotate = _FunctionType(annotate.__code__, globs, closure=closure)
    return new_annotate(1)


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

    # In 3.14 the 'canonical' method of getting annotations is to use __annotate__
    # If this doesn't exist, check __annotations__ and treat as 3.13 or earlier.
    annotate = ns.get("__annotate__")

    if annotate is not None:
        raw_annotations = call_annotate_func(annotate)
    else:
        raw_annotations = ns.get("__annotations__", {})

    # Unlike annotationlib we still try to evaluate string annotations
    # This will catch cases where someone has used a literal string for a
    # single attribute.
    if eval_str:
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

        annotations = {
            k: eval_hint(v, context)
            for k, v in raw_annotations.items()
        }

    else:
        annotations = raw_annotations.copy()

    return annotations


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

