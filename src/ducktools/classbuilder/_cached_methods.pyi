# This should only contain the types for the caches
import types
import typing as t

init_cache: dict[tuple[int, bool, bool], types.FunctionType]
eq_cache: dict[tuple[int], types.FunctionType]
repr_cache: dict[tuple[int], types.FunctionType]
replace_cache: dict[tuple[int], types.FunctionType]
hash_cache: dict[tuple[int], types.FunctionType]
setattr_cache: dict[tuple[t.Literal[0], bool], types.FunctionType]
delattr_cache: dict[tuple[t.Literal[0]], types.FunctionType]
