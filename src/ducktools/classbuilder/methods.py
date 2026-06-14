# MIT License
#
# Copyright (c) 2024-2026 David C Ellis
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

__lazy_modules__ = [
    "ducktools.classbuilder.annotations",
    "reprlib",
]

import builtins
import reprlib
try:
    from _types import (  # type: ignore
        FunctionType as _FunctionType,
        MappingProxyType as _MappingProxyType,
    )
except ImportError:
    from types import (
        FunctionType as _FunctionType,
        MappingProxyType as _MappingProxyType,
    )


from .annotations import apply_annotations
from .constants import INTERNALS_DICT, NOTHING, REPLACE_NAME
from .functions import get_fields, get_flags, get_methods

try:
    from ._cached_methods import init_cache, setattr_cache
except ImportError:  # pragma: nocover
    # Needed for generating cached methods after deletion
    init_cache = {}
    setattr_cache = {}


def _recursive_repr(func):
    # wrapper to handle calling recursive_repr()
    # without eagerly importing it.
    return reprlib.recursive_repr()(func)


def _exec_and_retrieve(source, globs):
    # Exec and retrieve a generated method
    # Returns the name of the method and the method as a tuple
    local_vars = {}
    exec(source, globs, local_vars)
    return local_vars.popitem()


class GeneratedCode:
    """
    This class provides a return value for the generated output from source code
    generators.
    """

    __slots__ = ("source_code", "globs", "annotations")

    def __init__(self, source_code, globs=None, annotations=None):
        """
        :param source_code: The source code to provide to ``exec`` to generate the method
        :param globs: A globals dictionary with any names needed within the function
        :param annotations: Annotations dictionary for the function signature
        """
        self.source_code = source_code
        self.globs = {} if globs is None else globs
        self.annotations = annotations

    def __repr__(self):
        first_source_line = self.source_code.split("\n")[0]
        return (
            f"GeneratorOutput(source_code='{first_source_line} ...', "
            f"globs={self.globs!r}, annotations={self.annotations!r})"
        )

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (
                self.source_code,
                self.globs,
                self.annotations,
            ) == (
                other.source_code,
                other.globs,
                other.annotations,
            )
        return NotImplemented

    def generate(self):
        _, method = _exec_and_retrieve(self.source_code, self.globs)
        if self.annotations:
            apply_annotations(method, self.annotations)
        return method


def _get_method(cls, name):
    try:
        methods = get_methods(cls)
    except TypeError:
        return None

    return methods.get(name, None)


class MethodMaker:
    """
    The descriptor class to place where methods should be generated.
    This delays the actual generation and `exec` until the method is needed.

    This is used to convert a code generator that returns code and a globals
    dictionary into a descriptor to assign on a generated class.
    """
    __slots__ = (
        "funcname",
        "code_generator",
        "cached_generator",
        "decorator",
    )
    def __init__(self, funcname, code_generator, *, cached_generator=None, decorator=None):
        """
        :param funcname: name of the generated function eg `__init__`
        :param code_generator: code generator function to operate on a class.
        :param cached_generator: a method generator that includes an internal cache
        :param decorator: a decorator to apply directly to method after it has been created
        :param cls: The class the decorator is being attached to
        """

        self.funcname = funcname
        self.code_generator = code_generator
        self.cached_generator = cached_generator
        self.decorator = decorator

    def __repr__(self):
        return f"<MethodMaker for {self.funcname!r} method>"

    def attach(self, cls):
        # Creates an `AttachedMethod` that attaches this `MethodMaker`
        # to the class as a descriptor
        method = _AttachedMethod(self, cls)
        setattr(cls, self.funcname, method)

    def generate(self, cls):
        # Generate and return a method for the given class
        method = None
        if self.cached_generator:
            # If the class is not supported by the cached generator, this returns
            # None to fall back to the standard generator.
            method = self.cached_generator(cls, funcname=self.funcname)

        if method is None:
            method = self.code_generator(cls, funcname=self.funcname).generate()

        # Patch up the method name and annotations
        try:
            method.__qualname__ = f"{cls.__qualname__}.{self.funcname}"
        except AttributeError:
            # This might be a property or some other special
            # descriptor. Don't try to rename.
            pass

        if self.decorator:
            method = self.decorator(method)

        return method


class _AttachedMethod:
    """
    Descriptor for attaching a method maker to a class.
    """
    __slots__ = ("maker", "cls")
    def __init__(self, maker, cls):
        self.maker = maker
        self.cls = cls

    def __repr__(self):
            return f"<_AttachedMethod for {self.maker.funcname!r} method on {self.cls.__qualname__!r}>"

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return (
            self.maker == other.maker
            and self.cls == other.cls
        )

    def __get__(self, inst, cls=None):
        method = self.maker.generate(self.cls)
        # Replace this descriptor on the class with the generated function
        setattr(self.cls, self.maker.funcname, method)

        # Use 'get' to return the generated function as a bound method
        # instead of as a regular function for first usage.
        return method.__get__(inst, cls)


# Argument getters for the generic cached methods
# The first argument should always be the list of argument names
# Other arguments can be boolean flags to pass to the cached methods
def get_empty_args(cls):
    # If argument names aren't used, we still need an empty tuple
    # for the first argument.
    return ((),)


def get_init_args(cls):
    fields = get_fields(cls)

    # keyword arguments need to be sorted at the end
    # in order to be correctly popped when used in the
    # method.
    field_args = []
    kw_field_args = []

    for name, f in fields.items():
        if f.default_factory is not NOTHING:
            return None
        if f.default is not NOTHING and not f.init:
            return None

        if f.init:
            if f.kw_only:
                kw_field_args.append(name)
            else:
                field_args.append(name)

    flags = get_flags(cls)
    slotted = flags.get("slotted", True)
    frozen = flags.get("frozen", True)
    field_names = (*field_args, *kw_field_args)
    return (field_names, frozen, frozen and slotted)


def get_compare_args(cls):
    return (tuple(k for k, v in get_fields(cls).items() if v.compare),)


def get_repr_args(cls):
    return (tuple(k for k, v in get_fields(cls).items() if v.repr),)


def get_replace_args(cls):
    return (tuple(k for k, v in get_fields(cls).items() if v.init),)


def get_frozen_setattr_args(cls):
    flags = get_flags(cls)
    slotted = flags.get("slotted", True)
    # The empty tuple is needed for the 0 arguments
    return ((), slotted)


# Globals getters for cached functions
def get_init_globals(cls):
    flags = get_flags(cls)
    globs = {}
    frozen = flags.get("frozen", True)
    slotted = flags.get("slotted", True)

    if frozen and slotted:
        globs["__object_setattr"] = object.__setattr__

    return globs


def get_frozen_setattr_globals(cls):
    flags = get_flags(cls)
    globs = {}
    globs["__field_names"] = set(get_fields(cls))

    # Better to be safe and use the method that works in both cases
    # if somehow slotted has not been set.
    if flags.get("slotted", True):
        globs["__setattr_func"] = object.__setattr__

    return globs


# Fix parameters in function signatures
def get_init_parameters(cls):
    """
    This takes a class and returns new
    co_varnames, co_argcount, co_kwonlyargcount, __defaults__ and __kwdefaults__, __annotations__

    These can be used to patch a basic `__init__` function to have new parameters
    and defaults.
    """
    fields = get_fields(cls)
    varnames = ["self"]
    kw_varnames = []
    argcount = 1  # self counts as an arg
    kwonlyargcount = 0
    defaults = []
    kwdefaults = {}
    annotations = {}

    for name, field in fields.items():
        # The actual checks for these are covered by get_init_args
        # These are the conditions under which cached init is not supported
        assert field.init or (field.default is NOTHING)
        assert field.default_factory is NOTHING

        if field.init:
            if field.kw_only:
                kw_varnames.append(name)
                kwonlyargcount += 1
                if field.default is not NOTHING:
                    kwdefaults[name] = field.default
            else:
                varnames.append(name)
                argcount += 1
                if field.default is not NOTHING:
                    defaults.append(field.default)

            if field._type is not NOTHING:
                annotations[name] = field._type

    varnames = (*varnames, *kw_varnames)

    if annotations:
        annotations["return"] = None

    defaults = tuple(defaults) if defaults else None
    kwdefaults = kwdefaults if kwdefaults else None

    return varnames, argcount, kwonlyargcount, defaults, kwdefaults, annotations


def _fix_consts(consts, active_pair, pairs):
    # Placeholders should be in order and only seen once
    # So if they are replaced, move to the next placeholder
    # and only compare one placeholder each time

    new_consts = []
    for const in consts:
        if active_pair:
            if isinstance(const, str):
                new_const = const.replace(*active_pair)
                if new_const != const:
                    try:
                        active_pair = pairs.pop()
                    except IndexError:
                        # All placeholders have been replaced
                        active_pair = None
            elif isinstance(const, tuple):
                new_const = _fix_consts(const, active_pair, pairs)
            else:
                new_const = const
        else:
            new_const = const

        # Append the new values
        new_consts.append(new_const)

    return tuple(new_consts)


def get_counter_field_names(argcount):
    return [f"{REPLACE_NAME}{i}_" for i in range(argcount)]


# Classes to handle cached methods
class _CacheStats:
    __slots__ = ("hits", "misses", "skips")

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.skips = 0

    @property
    def hit_percent(self):
        # If there are no cache hits, return 100%
        if (self.hits + self.misses) > 0:
            return (self.hits / (self.hits + self.misses)) * 100
        return 100

    def __repr__(self):
        return f"<CacheStats; hits: {self.hits}, misses: {self.misses}; {self.hit_percent:.1f}% cache hits; uncacheable: {self.skips}>"


class _SimpleCache:
    """
    A simple dictionary cache that only caches based on
    positional arguments. Keyword arguments are ignored
    for caching purposes.
    """

    __slots__ = ("_func", "_seed", "_stats")

    def __init__(self, func, *, cache_seed=None):
        self._func = func
        self._seed = {} if cache_seed is None else dict(cache_seed)
        self._stats = _CacheStats()

    def __repr__(self):
        return f"<{type(self).__name__} for {self._func}>"

    @property
    def stats(self):
        return self._stats

    @property
    def state(self):
        return _MappingProxyType(self._seed)

    def clear(self, new_cache=None):
        self._seed = {} if new_cache is None else dict(new_cache)
        self._stats = _CacheStats()

    def __call__(self, *args, **kwargs):
        try:
            result = self._seed[args]
            self._stats.hits += 1
        except KeyError:
            result = self._func(*args, **kwargs)
            self._seed[args] = result
            self._stats.misses += 1

        return result


def _simple_cache(*, cache_seed):
    def wrapper(func):
        return _SimpleCache(func, cache_seed=cache_seed)

    return wrapper


def counter_to_class_generator(
    counter_generator,
    argument_getter,
    globals_getter=None,
    *,
    cache=None,
    replace_strings=False,
    param_updater=None,
):
    # This takes a counting source generator and converts it into a function
    # generator with cached methods backing it
    @_simple_cache(cache_seed=cache)
    def source_exec(*args, funcname):
        gen = counter_generator(*args, funcname=funcname)
        method = gen.generate()
        return method

    def method_generator(cls, funcname):
        args = argument_getter(cls)

        if args is None:
            # If the argument getter returns None
            # the method is not cacheable
            source_exec.stats.skips += 1  # Add one to skip count
            return None

        # The first argument should always be a tuple of fields
        assert len(args) > 0

        fieldnames = args[0]
        fieldcount = len(args[0])
        exec_args = (fieldcount, *args[1:])

        raw_func = source_exec(*exec_args, funcname=funcname)

        arg_fixes = {f"{REPLACE_NAME}{i}_": arg for i, arg in enumerate(fieldnames)}

        # Get existing attribute names and strings
        co_names = raw_func.__code__.co_names
        co_consts = raw_func.__code__.co_consts

        # Skip patching if there are no field names to fix
        if arg_fixes:
            # Patch the attribute names (eg self.placeholder -> self.field_name)
            new_co_names = tuple(arg_fixes.get(name, name) for name in co_names)

            # Patch strings
            if replace_strings:
                fix_pairs = list(reversed(arg_fixes.items()))
                active_pair = fix_pairs.pop()
                new_co_consts = _fix_consts(co_consts, active_pair, fix_pairs)
            else:
                new_co_consts = co_consts
        else:
            new_co_names = co_names
            new_co_consts = co_consts

        if param_updater:
            varnames, argcount, kwonlyargcount, defaults, kwdefaults, annotations = (
                param_updater(cls)
            )
            original_varnames = raw_func.__code__.co_varnames
            if len(varnames) < len(original_varnames):
                # Extra locals are defined outside of the function signature
                # Add them to the end
                varnames = (*varnames, *original_varnames[len(varnames):])
        else:
            varnames = raw_func.__code__.co_varnames
            argcount = raw_func.__code__.co_argcount
            kwonlyargcount = raw_func.__code__.co_kwonlyargcount
            defaults = raw_func.__defaults__
            kwdefaults = raw_func.__kwdefaults__
            annotations = None

        globs = {} if globals_getter is None else globals_getter(cls)

        # The exec() call would normally insert this but it's not included automatically
        # by functiontype so make sure to add it here
        globs["__builtins__"] = builtins.__dict__

        method = _FunctionType(
            raw_func.__code__.replace(
                co_names=new_co_names,
                co_consts=new_co_consts,
                co_varnames=varnames,
                co_argcount=argcount,
                co_kwonlyargcount=kwonlyargcount,
            ),
            globs,
            name=funcname,
            argdefs=defaults,
            closure=raw_func.__closure__,
        )
        # Argument to FunctionType was only added in 3.13
        method.__kwdefaults__ = kwdefaults

        # Remove the module reference to avoid retrieving incorrect code
        method.__module__ = None  # type: ignore

        if annotations:
            apply_annotations(method, annotations)

        return method

    method_generator.cache = source_exec  # type: ignore

    return method_generator


def get_init_generator(null=NOTHING, extra_code=None):
    def cls_init_generator(cls, funcname="__init__"):
        fields = get_fields(cls)
        flags = get_flags(cls)

        frozen = flags.get("frozen", True)
        slotted = flags.get("slotted", True)

        arglist = []
        kw_only_arglist = []
        assignments = []
        kw_only_assignments = []
        globs = {}
        annotations = {}

        if frozen and slotted:
            globs["__object_setattr"] = object.__setattr__
        elif frozen:
            assignments.append("__classbuilder_selfdict = self.__dict__")

        for k, v in fields.items():
            if v.init:
                if v.default is not null:
                    globs[f"_{k}_default"] = v.default
                    arg = f"{k}=_{k}_default"
                    if frozen and slotted:
                        assignment = f"__object_setattr(self, {k!r}, {k})"
                    elif frozen:
                        assignment = f"__classbuilder_selfdict[{k!r}] = {k}"
                    else:
                        assignment = f"self.{k} = {k}"
                elif v.default_factory is not null:
                    globs[f"_{k}_factory"] = v.default_factory
                    arg = f"{k}=None"
                    if frozen and slotted:
                        assignment = f"__object_setattr(self, {k!r}, _{k}_factory() if {k} is None else {k})"
                    elif frozen:
                        assignment = f"__classbuilder_selfdict[{k!r}] = _{k}_factory() if {k} is None else {k}"
                    else:
                        assignment = f"self.{k} = _{k}_factory() if {k} is None else {k}"  # fmt: skip
                else:
                    arg = f"{k}"
                    if frozen and slotted:
                        assignment = f"__object_setattr(self, {k!r}, {k})"
                    elif frozen:
                        assignment = f"__classbuilder_selfdict[{k!r}] = {k}"
                    else:
                        assignment = f"self.{k} = {k}"

                if v.kw_only:
                    kw_only_arglist.append(arg)
                    kw_only_assignments.append(assignment)
                else:
                    arglist.append(arg)
                    assignments.append(assignment)

                if v._type is not NOTHING:
                    annotations[k] = v._type
            else:
                if v.default is not null:
                    globs[f"_{k}_default"] = v.default
                    if frozen and slotted:
                        assignment = f"__object_setattr(self, {k!r}, _{k}_default)"
                    elif frozen:
                        assignment = f"__classbuilder_selfdict[{k!r}] = _{k}_default"
                    else:
                        assignment = f"self.{k} = _{k}_default"
                    assignments.append(assignment)
                elif v.default_factory is not null:
                    globs[f"_{k}_factory"] = v.default_factory
                    if frozen and slotted:
                        assignment = f"__object_setattr(self, {k!r}, _{k}_factory())"
                    elif frozen:
                        assignment = f"__classbuilder_selfdict[{k!r}] = _{k}_factory()"
                    else:
                        assignment = f"self.{k} = _{k}_factory()"
                    assignments.append(assignment)

        pos_args = ", ".join(arglist)
        kw_args = ", ".join(kw_only_arglist)
        if pos_args and kw_args:
            args = f"{pos_args}, *, {kw_args}"
        elif kw_args:
            args = f"*, {kw_args}"
        else:
            args = pos_args

        assignments.extend(kw_only_assignments)

        assigns = "\n    ".join(assignments) if assignments else "pass\n"
        # fmt: off
        code = (
            f"def {funcname}(self, {args}):\n"
            f"    {assigns}\n"
        )
        # fmt: on

        # Handle additional function calls
        # Used for validate_field on fieldclasses
        if extra_code:
            for line in extra_code:
                code += f"    {line}\n"

        return GeneratedCode(code, globs)

    return cls_init_generator


class_init_generator = get_init_generator()


def generic_init_generator(field_names, frozen, frozen_and_slotted, *, funcname="__init__"):
    # Unlike the other generators, this only handles a subset of __init__ functions
    # those without default_factories or non-init defaults

    # Because slotted alone doesn't change the init, frozen_and_slotted
    # is used as a separate argument so slotted and unslotted unfrozen
    # classes share the same __init__ cache

    assignments = []
    if field_names and frozen and not frozen_and_slotted:
        assignments.append("__classbuilder_selfdict = self.__dict__")

    for f in field_names:
        if frozen_and_slotted:
            assignments.append(f"__object_setattr(self, {f!r}, {f})")
        elif frozen:
            assignments.append(f"__classbuilder_selfdict[{f!r}] = {f}")
        else:
            assignments.append(f"self.{f} = {f}")

    if field_names:
        params = "self, " + ", ".join(field_names)
    else:
        params = "self"

    if assignments:
        body = "\n    ".join(assignments)
    else:
        body = "pass"

    # fmt: off
    code = (
        f"def {funcname}({params}):\n"
        f"    {body}\n"
    )
    # fmt: on

    return GeneratedCode(code)


def _counter_init_generator(argcount, frozen, frozen_and_slotted, /, *, funcname="__init__"):
    field_names = get_counter_field_names(argcount)
    return generic_init_generator(field_names, frozen, frozen_and_slotted, funcname=funcname)


def generic_repr_generator(field_names, *, funcname="__repr__"):
    content = ", ".join(f"{name}={{self.{name}!r}}" for name in field_names)

    # fmt: off
    code = (
        f"def {funcname}(self):\n"
        f"    return f'{{type(self).__qualname__}}({content})'\n"
    )
    # fmt: on

    return GeneratedCode(code)


def class_repr_generator(cls, funcname="__repr__"):
    # For a regular class source, key and attrib names are the same
    field_names = [k for k, v in get_fields(cls).items() if v.repr]
    return generic_repr_generator(field_names, funcname=funcname)


def _counter_repr_generator(argcount, /, *, funcname="__repr__"):
    field_names = get_counter_field_names(argcount)
    return generic_repr_generator(field_names, funcname=funcname)


def generic_eq_generator(field_names, *, funcname="__eq__"):
    class_comparison = "self.__class__ is other.__class__"
    if field_names:
        instance_comparison = "\n        and ".join(
            f"self.{name} == other.{name}" for name in field_names
        )
    else:
        instance_comparison = "True"

    # fmt: off
    code = (
        f"def {funcname}(self, other):\n"
        f"    if self is other:\n"
        f"        return True\n"
        f"    return (\n"
        f"        {instance_comparison}\n"
        f"    ) if {class_comparison} else NotImplemented\n"
    )
    # fmt: on

    return GeneratedCode(code)


def class_eq_generator(cls, funcname="__eq__"):
    field_names = [name for name, attrib in get_fields(cls).items() if attrib.compare]

    return generic_eq_generator(field_names, funcname=funcname)


def _counter_eq_generator(argcount, /, *, funcname="__eq__"):
    # This is a cached accelerated eq generator
    # It returns uglier source, but the source can be cached
    # and reused more easily.
    field_names = get_counter_field_names(argcount)

    return generic_eq_generator(field_names, funcname=funcname)


def get_generic_order_generator(field_names, operator, *, funcname):
    class_comparison = "self.__class__ is other.__class__"
    # Equal objects should be False for gt/lt comparisons
    eq_return = "True" if "=" in operator else "False"

    instance_comparisons = [
        (
            f"        if self.{name} != other.{name}:\n"
            f"            return self.{name} {operator} other.{name}\n"
        )
        for name in field_names
    ]
    instance_comparisons.append(f"        return {eq_return}")

    instance_comparison = "".join(instance_comparisons)

    # fmt: off
    code = (
        f"def {funcname}(self, other):\n"
        f"    if self is other:\n"
        f"        return {eq_return}\n"
        f"    if {class_comparison}:\n"
        f"{instance_comparison}\n"
        f"    return NotImplemented\n"
    )
    # fmt: on

    return GeneratedCode(code)


def get_class_order_generator(cls, operator, *, funcname):
    field_names = [name for name, attrib in get_fields(cls).items() if attrib.compare]
    return get_generic_order_generator(field_names, operator, funcname=funcname)


def _get_counter_order_generator(argcount, operator, /, *, funcname):
    field_names = get_counter_field_names(argcount)
    return get_generic_order_generator(field_names, operator, funcname=funcname)


def class_lt_generator(cls, funcname="__lt__"):
    return get_class_order_generator(cls, "<", funcname=funcname)


def _counter_lt_generator(argcount, /, *, funcname="__lt__"):
    return _get_counter_order_generator(argcount, "<", funcname=funcname)


def class_le_generator(cls, funcname="__le__"):
    return get_class_order_generator(cls, "<=", funcname=funcname)


def _counter_le_generator(argcount, /, *, funcname="__le__"):
    return _get_counter_order_generator(argcount, "<=", funcname=funcname)


def class_gt_generator(cls, funcname="__gt__"):
    return get_class_order_generator(cls, ">", funcname=funcname)


def _counter_gt_generator(argcount, /, *, funcname="__gt__"):
    return _get_counter_order_generator(argcount, ">", funcname=funcname)


def class_ge_generator(cls, funcname="__ge__"):
    return get_class_order_generator(cls, ">=", funcname=funcname)


def _counter_ge_generator(argcount, /, *, funcname="__ge__"):
    return _get_counter_order_generator(argcount, ">=", funcname=funcname)


def generic_replace_generator(field_pairs, *, funcname="__replace__"):
    # This takes pairs of the init param name and the attribute
    # Needed to handle the replace method for Fields where the
    # param is `type` but the field name is `_type`
    if field_pairs:
        vals = ",\n".join(
            f"        '{param}': self.{attrib}"
            for param, attrib in field_pairs
        )  # fmt: skip

        init_dict = f"{{\n{vals},\n    }}"

        code = (
            f"def {funcname}(self, /, **changes):\n"
            f"    new_kwargs = {init_dict}\n"
            f"    new_kwargs |= changes\n"
            f"    return self.__class__(**new_kwargs)\n"
        )  # fmt: skip

    else:
        # There are no fields to keep, but may be init params
        # to pass forward.
        # This method is largely useless but exists for completeness
        code = (
            f"def {funcname}(self, /, **changes):\n"
            f"    return self.__class__(**changes)\n"
        )  # fmt: skip

    return GeneratedCode(code)


def class_replace_generator(cls, funcname="__replace__"):
    field_pairs = [(k, k) for k, v in get_fields(cls).items() if v.init]
    return generic_replace_generator(field_pairs, funcname=funcname)



def _counter_replace_generator(argcount, /, *, funcname="__replace__"):
    field_pairs = [(n, n) for n in get_counter_field_names(argcount)]
    return generic_replace_generator(field_pairs, funcname=funcname)


def generic_frozen_setattr_generator(slotted, *, funcname="__setattr__"):
    if slotted:
        setattr_method = "__setattr_func(self, name, value)"
        hasattr_check = "hasattr(self, name)"
    else:
        setattr_method = "self.__dict__[name] = value"
        hasattr_check = "name in self.__dict__"

    # fmt: off
    body = (
        f"    if {hasattr_check} or name not in __field_names:\n"
        f'        raise TypeError(\n'
        f'            f"{{type(self).__name__!r}} object does not support attribute assignment"\n'
        f'        )\n'
        f"    else:\n"
        f"        {setattr_method}\n"
    )
    # fmt: on
    code = f"def {funcname}(self, name, value):\n{body}"
    return GeneratedCode(code)


def _counter_frozen_setattr_generator(argcount, slotted, /, *, funcname="__setattr__"):
    return generic_frozen_setattr_generator(slotted, funcname=funcname)


def class_frozen_setattr_generator(cls, funcname="__setattr__"):
    globs = get_frozen_setattr_globals(cls)
    slotted = "__setattr_func" in globs
    gen = generic_frozen_setattr_generator(slotted, funcname=funcname)

    # Recreate the GeneratedCode object with the correct globals
    return GeneratedCode(gen.source_code, globs)


def generic_frozen_delattr_generator(*, funcname="__delattr__"):
    body = (
        '    raise TypeError(\n'
        '        f"{type(self).__name__!r} object does not support attribute deletion"\n'
        '    )\n'
    )  # fmt: skip
    code = f"def {funcname}(self, name):\n{body}"
    return GeneratedCode(code)


def _counter_frozen_delattr_generator(argcount, /, *, funcname="__delattr__"):
    # Argcount is needed for consistency but is ignored
    return generic_frozen_delattr_generator(funcname=funcname)


def class_frozen_delattr_generator(cls, funcname="__delattr__"):
    return generic_frozen_delattr_generator(funcname=funcname)


def generic_hash_generator(field_names, *, funcname="__hash__"):
    vals = ", ".join(f"self.{name}" for name in field_names)
    if len(field_names) == 1:
        # Needs a trailing comma for only 1 argument
        # to make a tuple
        vals += ","

    code = f"def {funcname}(self):\n    return hash(({vals}))\n"
    return GeneratedCode(code)


def _counter_hash_generator(argcount, /, *, funcname="__hash__"):
    field_names = get_counter_field_names(argcount)
    return generic_hash_generator(field_names, funcname=funcname)


def class_hash_generator(cls, funcname="__hash__"):
    field_names = [name for name, attrib in get_fields(cls).items() if attrib.compare]
    return generic_hash_generator(field_names, funcname=funcname)


# As only the __get__ method refers to the class we can use the same
# Descriptor instances for every class.
init_maker = MethodMaker(
    "__init__",
    class_init_generator,
    cached_generator=counter_to_class_generator(
        _counter_init_generator,
        get_init_args,
        globals_getter=get_init_globals,
        param_updater=get_init_parameters,
        replace_strings=True,
        cache=init_cache,
    ),
)
repr_maker = MethodMaker(
    "__repr__",
    class_repr_generator,
    cached_generator=counter_to_class_generator(
        _counter_repr_generator,
        get_repr_args,
        replace_strings=True,
    ),
    decorator=_recursive_repr,
)
eq_maker = MethodMaker(
    "__eq__",
    class_eq_generator,
    cached_generator=counter_to_class_generator(
        _counter_eq_generator,
        get_compare_args,
    ),
)
lt_maker = MethodMaker(
    "__lt__",
    class_lt_generator,
    cached_generator=counter_to_class_generator(
        _counter_lt_generator,
        get_compare_args,
    ),
)
le_maker = MethodMaker(
    "__le__",
    class_le_generator,
    cached_generator=counter_to_class_generator(
        _counter_le_generator,
        get_compare_args,
    ),
)
gt_maker = MethodMaker(
    "__gt__",
    class_gt_generator,
    cached_generator=counter_to_class_generator(
        _counter_gt_generator,
        get_compare_args,
    ),
)
ge_maker = MethodMaker(
    "__ge__",
    class_ge_generator,
    cached_generator=counter_to_class_generator(
        _counter_ge_generator,
        get_compare_args,
    ),
)
replace_maker = MethodMaker(
    "__replace__",
    class_replace_generator,
    cached_generator=counter_to_class_generator(
        _counter_replace_generator,
        get_replace_args,
        replace_strings=True,
    ),
)
frozen_setattr_maker = MethodMaker(
    "__setattr__",
    class_frozen_setattr_generator,
    cached_generator=counter_to_class_generator(
        _counter_frozen_setattr_generator,
        get_frozen_setattr_args,
        get_frozen_setattr_globals,
        cache=setattr_cache,
    ),
)
frozen_delattr_maker = MethodMaker(
    "__delattr__",
    class_frozen_delattr_generator,
    cached_generator=counter_to_class_generator(
        _counter_frozen_delattr_generator,
        get_empty_args,
    ),
)
hash_maker = MethodMaker(
    "__hash__",
    class_hash_generator,
    cached_generator=counter_to_class_generator(
        _counter_hash_generator,
        get_compare_args,
    ),
)


def add_methods(cls, methods, *, internals=None):
    """
    Unconditionally add methods to a class and update the internals dict

    :param methods: iterable of methods to add to a class
    :param internals: the classbuilder_internals dict of the class
                      this is used directly by `builder`
    :return: The complete current set of methods assigned to the class
    """
    if internals is None:
        try:
            internals = cls.__dict__[INTERNALS_DICT]
        except KeyError:
            raise TypeError(f"{cls} is not a classbuilder generated class")

    existing_methods = internals.get("methods", {})
    new_methods = {}

    for method in methods:
        method.attach(cls)
        new_methods[method.funcname] = method

    all_methods = _MappingProxyType(existing_methods | new_methods)

    # Update the internals dict
    internals["methods"] = all_methods

    return all_methods
