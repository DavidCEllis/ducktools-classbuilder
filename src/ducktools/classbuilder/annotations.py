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


class _LazyAnnotationLib:
    def __getattr__(self, item):
        global _lazyannotationlib
        import annotationlib  # type: ignore
        _lazyannotationlib = annotationlib
        return getattr(annotationlib, item)


_lazy_annotationlib = _LazyAnnotationLib()


def get_func_annotations(func):
    """
    Given a function, return the annotations dictionary

    :param func: function object
    :return: dictionary of annotations
    """
    # This method exists for use by prefab in getting annotations from
    # the __prefab_post_init__ function
    try:
        annotations = func.__annotations__
    except Exception:
        if sys.version_info >= (3, 14):
            annotations = _lazy_annotationlib.get_annotations(
                func,
                format=_lazy_annotationlib.Format.FORWARDREF,
            )
        else:
            raise

    return annotations


def get_ns_annotations(ns):
    """
    Given a class namespace, attempt to retrieve the
    annotations dictionary.

    :param ns: Class namespace (eg cls.__dict__)
    :return: dictionary of annotations
    """

    annotations = ns.get("__annotations__")
    if annotations is not None:
        annotations = annotations.copy()
    elif sys.version_info >= (3, 14):
        # See if we're using PEP-649 annotations
        annotate = _lazy_annotationlib.get_annotate_from_class_namespace(ns)
        if annotate:
            annotations = _lazy_annotationlib.call_annotate_function(
                annotate,
                format=_lazy_annotationlib.Format.FORWARDREF
            )

    if annotations is None:
        annotations = {}

    return annotations


def is_classvar(hint):
    if isinstance(hint, str):
        # String annotations, just check if the string 'ClassVar' is in there
        # This is overly broad and could be smarter.
        return "ClassVar" in hint
    elif (annotationlib := sys.modules.get("annotationlib")) and isinstance(hint, annotationlib.ForwardRef):
        return "ClassVar" in hint.__arg__
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
