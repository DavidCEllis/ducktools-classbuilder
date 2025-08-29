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

try:
    from _types import FunctionType as _FunctionType, CellType as _CellType # type: ignore
except ImportError:
    from types import FunctionType as _FunctionType, CellType as _CellType

class _LazyAnnotationLib:
    def __getattr__(self, item):
        global _lazy_annotationlib
        import annotationlib  # type: ignore
        _lazy_annotationlib = annotationlib
        return getattr(annotationlib, item)


_lazy_annotationlib = _LazyAnnotationLib()


def _build_closure(annotate, owner, is_class, stringifier_dict, *, allow_evaluation):
    # Looks like Jelle might be changing the return type, copy this in here for now.
    if not annotate.__closure__:
        return None
    freevars = annotate.__code__.co_freevars
    new_closure = []
    for i, cell in enumerate(annotate.__closure__):
        if i < len(freevars):
            name = freevars[i]
        else:
            name = "__cell__"
        new_cell = None
        if allow_evaluation:
            try:
                cell.cell_contents
            except ValueError:
                pass
            else:
                new_cell = cell
        if new_cell is None:
            fwdref = _lazy_annotationlib._Stringifier(
                name,
                cell=cell,
                owner=owner,
                globals=annotate.__globals__,
                is_class=is_class,
                stringifier_dict=stringifier_dict,
            )
            stringifier_dict.stringifiers.append(fwdref)
            new_cell = _CellType(fwdref)
        new_closure.append(new_cell)
    return tuple(new_closure)


def _call_annotate_forwardrefs(annotate, *, owner=None):
    # Get all annotations as unevaluated forward references
    # Logic taken from the call_annotate_function logic

    is_class = isinstance(owner, type)

    # Attempt to call with VALUE_WITH_FAKE_GLOBALS
    # If this fails with a NotImplementedError then return
    # the FORWARDREF format as the best we can do as this means
    # the fake globals method can't be applied.
    try:
        annotate(_lazy_annotationlib.Format.VALUE_WITH_FAKE_GLOBALS)
    except NotImplementedError:
        return _lazy_annotationlib.call_annotate_function(
            annotate,
            format=_lazy_annotationlib.Format.FORWARDREF,
            owner=owner,
        )
    except Exception:
        pass

    globals = _lazy_annotationlib._StringifierDict(
        {},
        globals=annotate.__globals__,
        owner=owner,
        is_class=is_class,
        format=format,
    )
    closure = _build_closure(
        annotate, owner, is_class, globals, allow_evaluation=False
    )
    func = _FunctionType(
        annotate.__code__,
        globals,
        closure=closure,
        argdefs=annotate.__defaults__,
        kwdefaults=annotate.__kwdefaults__,
    )
    result = func(_lazy_annotationlib.Format.VALUE_WITH_FAKE_GLOBALS)

    globals.transmogrify()

    return result


def make_annotate_func(annos):
    type_repr = _lazy_annotationlib.type_repr
    Format = _lazy_annotationlib.Format

    # Construct an annotation function from __annotations__
    def __annotate__(format, /):
        if format in {Format.VALUE, Format.FORWARDREF, Format.STRING}:
            new_annos = {}
            for k, v in annos.items():
                v = evaluate_forwardref(v, format=format)
                if not isinstance(v, str) and format == Format.STRING:
                    v = type_repr(v)
                new_annos[k] = v
            return new_annos
        else:
            raise NotImplementedError(format)

    return __annotate__


def is_forwardref(obj):
    return isinstance(obj, _lazy_annotationlib.ForwardRef)


def evaluate_forwardref(ref, format=None):
    # A special forwardref evaluation that tries to include closure variables if they exist
    # It also places globals in the locals dict to assist in partial evaluation
    if isinstance(ref, str):
        return ref
    elif is_forwardref(ref):
        format = _lazy_annotationlib.Format.FORWARDREF if format is None else format

        if (owner := ref.__owner__):
            annotate = owner.__annotate__

            # Add globals first
            closure_and_locals = {**annotate.__globals__}
            if annotate.__closure__:
                for name, value in zip(annotate.__code__.co_freevars, annotate.__closure__):
                    try:
                        closure_and_locals[name] = value.cell_contents
                    except ValueError:
                        pass

            closure_and_locals.update(vars(owner))

            return ref.evaluate(
                globals=annotate.__globals__,
                locals=closure_and_locals,
                format=format
            )
        else:
            return ref.evaluate(format=format)

    return ref


def get_func_annotations(func):
    """
    Given a function, return the annotations dictionary

    :param func: function object
    :return: dictionary of annotations
    """
    # functions have '__annotations__' defined so check for '__annotate__' instead
    if annotate := getattr(func, "__annotate__", None):
        annotations = _call_annotate_forwardrefs(annotate, owner=func)
    else:
        annotations = getattr(func, "__annotations__", {}).copy()

    return annotations


def get_ns_annotations(ns, cls=None):
    """
    Given a class namespace, attempt to retrieve the
    annotations dictionary.

    :param ns: Class namespace (eg cls.__dict__)
    :param cls: Class if available
    :return: dictionary of annotations
    """

    annotations = ns.get("__annotations__")
    if annotations is not None:
        annotations = annotations.copy()
    else:
        # See if we're using PEP-649 annotations
        annotate = _lazy_annotationlib.get_annotate_from_class_namespace(ns)
        if annotate:
            if cls is None:
                annotations = _call_annotate_forwardrefs(annotate)
            else:
                annotations = _call_annotate_forwardrefs(annotate, owner=cls)

    if annotations is None:
        annotations = {}

    return annotations
