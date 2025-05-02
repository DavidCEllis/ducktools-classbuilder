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
    def __init__(self):
        if sys.version_info < (3, 14):
            self.annotationlib_unavailable = True
        else:
            self.annotationlib_unavailable = None

    def __getattr__(self, item):
        if self.annotationlib_unavailable:
            raise ImportError("'annotationlib' is not available")

        try:
            import annotationlib
        except ImportError:
            self.annotationlib_unavailable = True
            raise ImportError("'annotationlib' is not available")
        else:
            self.Format = annotationlib.Format
            self.call_annotate_function = annotationlib.call_annotate_function

            # This function keeps getting changed and renamed
            get_ns_annotate = getattr(annotationlib, "get_annotate_from_class_namespace", None)
            if get_ns_annotate is None:
                get_ns_annotate = getattr(annotationlib, "get_annotate_function")
            self.get_ns_annotate = get_ns_annotate

            if item == "Format":
                return self.Format
            elif item == "call_annotate_function":
                return self.call_annotate_function
            elif item == "get_ns_annotate":
                return get_ns_annotate

        raise AttributeError(f"{item!r} is not available from this lazy importer")

_lazy_annotationlib = _LazyAnnotationLib()


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
    else:
        try:
            # See if we're using PEP-649 annotations
            annotate = ns.get("__annotate__")  # Works in the early alphas
            if not annotate:
                annotate = _lazy_annotationlib.get_ns_annotate(ns)
            if annotate:
                annotations = _lazy_annotationlib.call_annotate_function(
                    annotate,
                    format=_lazy_annotationlib.Format.FORWARDREF
                )
        except ImportError:
            pass

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

