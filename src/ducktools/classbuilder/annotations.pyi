from collections.abc import Callable
import typing
import types
import sys

_CopiableMappings = dict[str, typing.Any] | types.MappingProxyType[str, typing.Any]

if sys.version_info >= (3, 14):
    from annotationlib import ForwardRef, Format

    # def get_ns_forwardrefs(ns: _CopiableMappings) -> dict[str, ForwardRef]: ...

    @typing.overload
    def evaluate_forwardref(ref: ForwardRef, format: Format | None = ...) -> ForwardRef | typing.Any: ...
    @typing.overload
    def evaluate_forwardref(ref: str, format: Format | None = ...) -> str: ...

    def is_forwardref(obj: object) -> bool: ...

    def make_annotate_func(
        cls: type,
        annos: dict[str, typing.Any],
        extra_annotation_func: types.FunctionType | None = ...,
    ) -> Callable[[int], dict[str, typing.Any]]: ...

else:
    # def get_ns_forwardrefs(ns: _CopiableMappings) -> dict: ...  # Actually always empty
    def evaluate_forwardref[T](ref: T, format: None = None) -> T: ...
    def is_forwardref(obj: object) -> typing.Literal[False]: ...
    def make_annotate_func(cls: type, annos: dict[str, typing.Any]) -> typing.Never: ...


def get_func_annotations(
    func: types.FunctionType,
) -> dict[str, typing.Any]: ...

def get_ns_annotations(
    ns: _CopiableMappings,
) -> dict[str, typing.Any]: ...

def is_classvar(
    hint: object,
) -> bool: ...
