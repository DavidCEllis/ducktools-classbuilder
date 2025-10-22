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

"""
Python 3.14 has new annotations methods, but does not provide any correct way to handle VALUE
annotation generation for new __init__ methods.

The approach taken here is to try to use VALUE annotations, if those fail it falls back to
STRING annotations, as if __future__ annotations actually arrived.

Hopefully in a future version of Python we will have complete, correct, performant annotations
so we can use a more standard format.
"""

class _LazyAnnotationLib:
    def __getattr__(self, item):
        global _lazy_annotationlib
        import annotationlib  # type: ignore
        _lazy_annotationlib = annotationlib
        return getattr(annotationlib, item)


_lazy_annotationlib = _LazyAnnotationLib()


def get_func_annotations(func, use_forwardref=False):
    """
    Given a function, return the annotations dictionary

    :param func: function object
    :return: dictionary of annotations
    """
    # Try to get `__annotations__` for VALUE annotations first
    try:
        raw_annotations = func.__annotations__
    except Exception:
        fmt = (
            _lazy_annotationlib.Format.FORWARDREF
            if use_forwardref
            else _lazy_annotationlib.Format.STRING
        )
        annotations = _lazy_annotationlib.get_annotations(func, format=fmt)
    else:
        annotations = raw_annotations.copy()

    return annotations


def get_ns_annotations(ns, cls=None, use_forwardref=False):
    """
    Given a class namespace, attempt to retrieve the
    annotations dictionary.

    :param ns: Class namespace (eg cls.__dict__)
    :param cls: Class if available
    :param use_forwardref: Use FORWARDREF instead of STRING if VALUE fails
    :return: dictionary of annotations
    """

    annotations = ns.get("__annotations__")
    if annotations is not None:
        annotations = annotations.copy()
    else:
        # See if we're using PEP-649 annotations
        annotate = _lazy_annotationlib.get_annotate_from_class_namespace(ns)
        if annotate:
            try:
                annotations = annotate(_lazy_annotationlib.Format.VALUE)
            except Exception:
                fmt = (
                    _lazy_annotationlib.Format.FORWARDREF
                    if use_forwardref
                    else _lazy_annotationlib.Format.STRING
                )

                annotations = _lazy_annotationlib.call_annotate_function(
                    annotate,
                    format=fmt,
                    owner=cls
                )

    if annotations is None:
        annotations = {}

    return annotations
