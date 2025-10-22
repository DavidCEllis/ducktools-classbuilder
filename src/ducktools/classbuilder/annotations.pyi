from collections.abc import Callable
import typing
import types
import sys

_CopiableMappings = dict[str, typing.Any] | types.MappingProxyType[str, typing.Any]

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
