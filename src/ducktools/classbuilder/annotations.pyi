import typing
import types

_T = typing.TypeVar("_T")
_CopiableMappings = dict[str, typing.Any] | types.MappingProxyType[str, typing.Any]

class _StringGlobs:
    def __missing__(self, key: _T) -> _T: ...


def eval_hint(
    hint: type | str,
    context: None | dict[str, typing.Any] = None,
) -> type | str: ...


def get_ns_annotations(
    ns: _CopiableMappings,
    eval_str: bool = True,
) -> dict[str, typing.Any]: ...

def is_classvar(
    hint: object,
) -> bool: ...
