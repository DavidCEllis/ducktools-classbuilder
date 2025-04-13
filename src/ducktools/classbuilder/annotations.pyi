import typing
import types

_CopiableMappings = dict[str, typing.Any] | types.MappingProxyType[str, typing.Any]

def get_ns_annotations(
    ns: _CopiableMappings,
) -> dict[str, typing.Any]: ...

def is_classvar(
    hint: object,
) -> bool: ...
