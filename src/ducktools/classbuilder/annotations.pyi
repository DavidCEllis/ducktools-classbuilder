import sys
import typing
import types

_CopiableMappings = dict[str, typing.Any] | types.MappingProxyType[str, typing.Any]

def get_func_annotations(
    func: types.FunctionType,
) -> dict[str, typing.Any]: ...

def get_ns_annotations(
    ns: _CopiableMappings,
    cls: type | None = ...,
) -> dict[str, typing.Any]: ...

def is_classvar(
    hint: object,
) -> bool: ...

def resolve_type(object, deferred_as_str: bool = ...) -> object: ...

def apply_annotations(obj: typing.Any, annotations: dict[str, typing.Any]) -> None: ...

def is_type(hint: str | object, t: type) -> bool: ...


if sys.version_info >= (3, 14):
    from reannotate import DeferredAnnotation
    @typing.overload
    def replace_generics_with_arg(hint: DeferredAnnotation) -> DeferredAnnotation: ...

    @typing.overload
    def replace_generics_with_arg(hint: str) -> str: ...

    @typing.overload
    def replace_generics_with_arg(hint: typing.Any) -> typing.Any: ...
else:
    @typing.overload
    def replace_generics_with_arg(hint: str) -> str: ...

    @typing.overload
    def replace_generics_with_arg(hint: typing.Any) -> typing.Any: ...
