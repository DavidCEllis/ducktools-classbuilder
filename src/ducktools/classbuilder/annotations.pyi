import typing
import types

_CopiableMappings = dict[str, typing.Any] | types.MappingProxyType[str, typing.Any]

_T = typing.TypeVar("_T")

def get_func_annotations(
    func: types.FunctionType,
    use_forwardref: bool = ...,
) -> dict[str, typing.Any]: ...

def get_ns_annotations(
    ns: _CopiableMappings,
    cls: type | None = ...,
    use_forwardref: bool = ...,
) -> dict[str, typing.Any]: ...

def is_classvar(
    hint: object,
) -> bool: ...

def resolve_type(object, deferred_as_str: bool = ...) -> object: ...

def apply_annotations(obj: typing.Any, annotations: dict[str, typing.Any]) -> None: ...
