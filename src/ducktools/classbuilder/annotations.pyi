import typing
import types


_CopiableMappings = dict[str, typing.Any] | types.MappingProxyType[str, typing.Any]

def eval_hint(
    hint: type | str,
    obj_globals: None | dict[str, typing.Any] = None,
    obj_locals: None | dict[str, typing.Any] = None,
) -> type | str: ...

def get_annotations(
    ns: _CopiableMappings,
    eval_str: bool = True,
) -> dict[str, typing.Any]: ...

def is_classvar(
    hint: object,
) -> bool: ...
