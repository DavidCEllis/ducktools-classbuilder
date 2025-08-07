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
A 'prebuilt' implementation of class generation.

Includes pre and post init functions along with other methods.
"""
from . import (
    INTERNALS_DICT, NOTHING, FIELD_NOTHING,
    Field, MethodMaker, GatheredFields, GeneratedCode, SlotMakerMeta,
    builder, get_flags, get_fields,
    make_unified_gatherer,
    eq_maker, frozen_setattr_maker, frozen_delattr_maker, replace_maker,
    get_repr_generator,
)

from .annotations import get_func_annotations

# These aren't used but are re-exported for ease of use
# noinspection PyUnresolvedReferences
from . import SlotFields, KW_ONLY  # noqa: F401

PREFAB_FIELDS = "PREFAB_FIELDS"
PREFAB_INIT_FUNC = "__prefab_init__"
PRE_INIT_FUNC = "__prefab_pre_init__"
POST_INIT_FUNC = "__prefab_post_init__"


class PrefabError(Exception):
    pass


def get_attributes(cls):
    """
    Copy of get_fields, typed to return Attribute instead of Field.
    This is used in the prefab methods.

    :param cls: class built with _make_prefab
    :return: dict[str, Attribute] of all gathered attributes
    """
    return getattr(cls, INTERNALS_DICT)["fields"]


# Method Generators
def init_generator(cls, funcname="__init__"):
    globs = {}
    # Get the internals dictionary and prepare attributes
    attributes = get_attributes(cls)
    flags = get_flags(cls)

    kw_only = flags.get("kw_only", False)

    # Handle pre/post init first - post_init can change types for __init__
    # Get pre and post init arguments
    pre_init_args = []
    post_init_args = []
    post_init_annotations = {}

    for extra_funcname, func_arglist in [
        (PRE_INIT_FUNC, pre_init_args),
        (POST_INIT_FUNC, post_init_args),
    ]:
        try:
            func = getattr(cls, extra_funcname)
            func_code = func.__code__
        except AttributeError:
            pass
        else:
            argcount = func_code.co_argcount + func_code.co_kwonlyargcount

            # Identify if method is static, if so include first arg, otherwise skip
            is_static = type(cls.__dict__.get(extra_funcname)) is staticmethod

            arglist = (
                func_code.co_varnames[:argcount]
                if is_static
                else func_code.co_varnames[1:argcount]
            )

            func_arglist.extend(arglist)

            if extra_funcname == POST_INIT_FUNC:
                post_init_annotations.update(get_func_annotations(func))

    pos_arglist = []
    kw_only_arglist = []
    for name, attrib in attributes.items():
        # post_init annotations can be used to broaden types.
        if name in post_init_annotations:
            globs[f"_{name}_type"] = post_init_annotations[name]
        elif attrib.type is not NOTHING:
            globs[f"_{name}_type"] = attrib.type

        if attrib.init:
            if attrib.default is not NOTHING:
                if isinstance(attrib.default, (str, int, float, bool)):
                    # Just use the literal in these cases
                    if attrib.type is NOTHING:
                        arg = f"{name}={attrib.default!r}"
                    else:
                        arg = f"{name}: _{name}_type = {attrib.default!r}"
                else:
                    # No guarantee repr will work for other objects
                    # so store the value in a variable and put it
                    # in the globals dict for eval
                    if attrib.type is NOTHING:
                        arg = f"{name}=_{name}_default"
                    else:
                        arg = f"{name}: _{name}_type = _{name}_default"
                    globs[f"_{name}_default"] = attrib.default
            elif attrib.default_factory is not NOTHING:
                # Use NONE here and call the factory later
                # This matches the behaviour of compiled
                if attrib.type is NOTHING:
                    arg = f"{name}=None"
                else:
                    arg = f"{name}: _{name}_type = None"
                globs[f"_{name}_factory"] = attrib.default_factory
            else:
                if attrib.type is NOTHING:
                    arg = name
                else:
                    arg = f"{name}: _{name}_type"
            if attrib.kw_only or kw_only:
                kw_only_arglist.append(arg)
            else:
                pos_arglist.append(arg)
        # Not in init, but need to set defaults
        else:
            if attrib.default is not NOTHING:
                globs[f"_{name}_default"] = attrib.default
            elif attrib.default_factory is not NOTHING:
                globs[f"_{name}_factory"] = attrib.default_factory

    pos_args = ", ".join(pos_arglist)
    kw_args = ", ".join(kw_only_arglist)
    if pos_args and kw_args:
        args = f"{pos_args}, *, {kw_args}"
    elif kw_args:
        args = f"*, {kw_args}"
    else:
        args = pos_args

    assignments = []
    processes = []  # post_init values still need default factories to be called.
    for name, attrib in attributes.items():
        if attrib.init:
            if attrib.default_factory is not NOTHING:
                value = f"{name} if {name} is not None else _{name}_factory()"
            else:
                value = name
        else:
            if attrib.default_factory is not NOTHING:
                value = f"_{name}_factory()"
            elif attrib.default is not NOTHING:
                value = f"_{name}_default"
            else:
                value = None

        if name in post_init_args:
            if attrib.default_factory is not NOTHING:
                processes.append((name, value))
        elif value is not None:
            assignments.append((name, value))

    if hasattr(cls, PRE_INIT_FUNC):
        pre_init_arg_call = ", ".join(f"{name}={name}" for name in pre_init_args)
        pre_init_call = f"    self.{PRE_INIT_FUNC}({pre_init_arg_call})\n"
    else:
        pre_init_call = ""

    if assignments or processes:
        body = ""
        body += "\n".join(
            f"    self.{name} = {value}" for name, value in assignments
        )
        body += "\n"
        body += "\n".join(f"    {name} = {value}" for name, value in processes)
    else:
        body = "    pass"

    if hasattr(cls, POST_INIT_FUNC):
        post_init_arg_call = ", ".join(f"{name}={name}" for name in post_init_args)
        post_init_call = f"    self.{POST_INIT_FUNC}({post_init_arg_call})\n"
    else:
        post_init_call = ""

    code = (
        f"def {funcname}(self, {args}) -> None:\n"
        f"{pre_init_call}\n"
        f"{body}\n"
        f"{post_init_call}\n"
    )

    return GeneratedCode(code, globs)


def iter_generator(cls, funcname="__iter__"):
    fields = get_attributes(cls)

    valid_fields = (
        name for name, attrib in fields.items()
        if attrib.iter
    )

    values = "\n".join(f"    yield self.{name}" for name in valid_fields)

    # if values is an empty string
    if not values:
        values = "    yield from ()"

    code = f"def {funcname}(self):\n{values}"
    globs = {}
    return GeneratedCode(code, globs)


def as_dict_generator(cls, funcname="as_dict"):
    fields = get_attributes(cls)

    vals = ", ".join(
        f"'{name}': self.{name}"
        for name, attrib in fields.items()
        if attrib.serialize
    )
    out_dict = f"{{{vals}}}"
    code = f"def {funcname}(self): return {out_dict}\n"

    globs = {}
    return GeneratedCode(code, globs)


def hash_generator(cls, funcname="__hash__"):
    fields = get_attributes(cls)
    vals = ", ".join(
        f"self.{name}"
        for name, attrib in fields.items()
        if attrib.compare
    )
    code = f"def {funcname}(self): return hash(({vals}))\n"
    globs = {}
    return GeneratedCode(code, globs)


init_maker = MethodMaker("__init__", init_generator)
prefab_init_maker = MethodMaker(PREFAB_INIT_FUNC, init_generator)
repr_maker = MethodMaker(
    "__repr__",
    get_repr_generator(recursion_safe=False, eval_safe=True)
)
recursive_repr_maker = MethodMaker(
    "__repr__",
    get_repr_generator(recursion_safe=True, eval_safe=True)
)
iter_maker = MethodMaker("__iter__", iter_generator)
asdict_maker = MethodMaker("as_dict", as_dict_generator)
hash_maker = MethodMaker("__hash__", hash_generator)


# Updated field with additional attributes
class Attribute(Field):
    """
    Get an object to define a prefab attribute

    :param default: Default value for this attribute
    :param default_factory: 0 argument callable to give a default value
                            (for otherwise mutable defaults, eg: list)
    :param init: Include this attribute in the __init__ parameters
    :param repr: Include this attribute in the class __repr__
    :param compare: Include this attribute in the class __eq__
    :param iter: Include this attribute in the class __iter__ if generated
    :param kw_only: Make this argument keyword only in init
    :param serialize: Include this attribute in methods that serialize to dict
    :param doc: Parameter documentation for slotted classes
    :param metadata: Additional non-construction related metadata
    :param type: Type of this attribute (for slotted classes)
    """
    iter: bool = True
    serialize: bool = True
    metadata: dict = Field(default=FIELD_NOTHING, default_factory=dict)  # type: ignore


# noinspection PyShadowingBuiltins
def attribute(
    *,
    default=NOTHING,
    default_factory=NOTHING,
    init=True,
    repr=True,
    compare=True,
    iter=True,
    kw_only=False,
    serialize=True,
    exclude_field=False,
    private=False,
    doc=None,
    metadata=None,
    type=NOTHING,
):
    """
    Helper function to get an object to define a prefab Attribute

    :param default: Default value for this attribute
    :param default_factory: 0 argument callable to give a default value
                            (for otherwise mutable defaults, eg: list)
    :param init: Include this attribute in the __init__ parameters
    :param repr: Include this attribute in the class __repr__
    :param compare: Include this attribute in the class __eq__
    :param iter: Include this attribute in the class __iter__ if generated
    :param kw_only: Make this argument keyword only in init
    :param serialize: Include this attribute in methods that serialize to dict
    :param exclude_field: Shorthand for setting repr, compare, iter and serialize to False
    :param private: Short for init, repr, compare, iter, serialize = False, must have default or factory
    :param doc: Parameter documentation for slotted classes
    :param metadata: Dictionary for additional non-construction metadata
    :param type: Type of this attribute (for slotted classes)

    :return: Attribute generated with these parameters.
    """
    if exclude_field:
        repr = False
        compare = False
        iter = False
        serialize = False

    if private:
        if default is NOTHING and default_factory is NOTHING:
            raise AttributeError("Private attributes must have defaults or factories.")
        init = False
        repr = False
        compare = False
        iter = False
        serialize = False

    return Attribute(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        compare=compare,
        iter=iter,
        kw_only=kw_only,
        serialize=serialize,
        doc=doc,
        type=type,
        metadata=metadata,
    )


prefab_gatherer = make_unified_gatherer(Attribute, False)


# Class Builders
# noinspection PyShadowingBuiltins
def _make_prefab(
    cls,
    *,
    init=True,
    repr=True,
    eq=True,
    iter=False,
    match_args=True,
    kw_only=False,
    frozen=False,
    dict_method=False,
    recursive_repr=False,
    gathered_fields=None,
):
    """
    Generate boilerplate code for dunder methods in a class.

    :param cls: Class to convert to a prefab
    :param init: generate __init__
    :param repr: generate __repr__
    :param eq: generate __eq__
    :param iter: generate __iter__
    :param match_args: generate __match_args__
    :param kw_only: Make all attributes keyword only
    :param frozen: Prevent attribute values from being changed once defined
                   (This does not prevent the modification of mutable attributes
                   such as lists)
    :param dict_method: Include an as_dict method for faster dictionary creation
    :param recursive_repr: Safely handle repr in case of recursion
    :param gathered_fields: Pre-gathered fields callable, to skip re-collecting attributes
    :return: class with __ methods defined
    """
    cls_dict = cls.__dict__

    if INTERNALS_DICT in cls_dict:
        raise PrefabError(
            f"Decorated class {cls.__name__!r} "
            f"has already been processed as a Prefab."
        )

    slots = cls_dict.get("__slots__")

    slotted = False if slots is None else True

    if gathered_fields is None:
        gatherer = prefab_gatherer
    else:
        gatherer = gathered_fields

    methods = set()

    if init and "__init__" not in cls_dict:
        methods.add(init_maker)
    else:
        methods.add(prefab_init_maker)

    if repr and "__repr__" not in cls_dict:
        if recursive_repr:
            methods.add(recursive_repr_maker)
        else:
            methods.add(repr_maker)
    if eq and "__eq__" not in cls_dict:
        methods.add(eq_maker)
    if iter and "__iter__" not in cls_dict:
        methods.add(iter_maker)
    if frozen:
        methods.add(frozen_setattr_maker)
        methods.add(frozen_delattr_maker)
        methods.add(hash_maker)
    if dict_method:
        methods.add(asdict_maker)

    methods.add(replace_maker)

    flags = {
        "kw_only": kw_only,
        "slotted": slotted,
    }

    cls = builder(
        cls,
        gatherer=gatherer,
        methods=methods,
        flags=flags,
    )

    # Get fields now the class has been built
    fields = get_fields(cls)

    # Check pre_init and post_init functions if they exist
    try:
        func = getattr(cls, PRE_INIT_FUNC)
        func_code = func.__code__
    except AttributeError:
        pass
    else:
        if func_code.co_posonlyargcount > 0:
            raise PrefabError(
                "Positional only arguments are not supported in pre or post init functions."
            )

        argcount = func_code.co_argcount + func_code.co_kwonlyargcount

        # Include the first argument if the method is static
        is_static = type(cls.__dict__.get(PRE_INIT_FUNC)) is staticmethod

        arglist = (
            func_code.co_varnames[:argcount]
            if is_static
            else func_code.co_varnames[1:argcount]
        )

        for item in arglist:
            if item not in fields.keys():
                raise PrefabError(
                    f"{item} argument in {PRE_INIT_FUNC} is not a valid attribute."
                )

    post_init_args = []
    try:
        func = getattr(cls, POST_INIT_FUNC)
        func_code = func.__code__
    except AttributeError:
        pass
    else:
        if func_code.co_posonlyargcount > 0:
            raise PrefabError(
                "Positional only arguments are not supported in pre or post init functions."
            )

        argcount = func_code.co_argcount + func_code.co_kwonlyargcount

        # Include the first argument if the method is static
        is_static = type(cls.__dict__.get(POST_INIT_FUNC)) is staticmethod

        arglist = (
            func_code.co_varnames[:argcount]
            if is_static
            else func_code.co_varnames[1:argcount]
        )

        for item in arglist:
            if item not in fields.keys():
                raise PrefabError(
                    f"{item} argument in {POST_INIT_FUNC} is not a valid attribute."
                )

        post_init_args.extend(arglist)

    # Gather values for match_args and do some syntax checking
    default_defined = []
    valid_args = list(fields.keys())

    for name, attrib in fields.items():
        # slot_gather and parent classes may use Fields
        # prefabs require Attributes, so convert.
        if not isinstance(attrib, Attribute):
            attrib = Attribute.from_field(attrib)
            fields[name] = attrib

        if not kw_only:
            # Syntax check arguments for __init__ don't have non-default after default
            if attrib.init and not attrib.kw_only:
                if attrib.default is not NOTHING or attrib.default_factory is not NOTHING:
                    default_defined.append(name)
                else:
                    if default_defined:
                        names = ", ".join(default_defined)
                        raise SyntaxError(
                            "non-default argument follows default argument",
                            f"defaults: {names}",
                            f"non_default after default: {name}",
                        )

    setattr(cls, PREFAB_FIELDS, valid_args)

    if match_args and "__match_args__" not in cls_dict:
        setattr(cls, "__match_args__", tuple(valid_args))

    return cls


class Prefab(metaclass=SlotMakerMeta, gatherer=prefab_gatherer):
    __slots__ = {}  # type: ignore

    # noinspection PyShadowingBuiltins
    def __init_subclass__(
        cls,
        init=True,
        repr=True,
        eq=True,
        iter=False,
        match_args=True,
        kw_only=False,
        frozen=False,
        dict_method=False,
        recursive_repr=False,
    ):
        _make_prefab(
            cls,
            init=init,
            repr=repr,
            eq=eq,
            iter=iter,
            match_args=match_args,
            kw_only=kw_only,
            frozen=frozen,
            dict_method=dict_method,
            recursive_repr=recursive_repr,
        )


# noinspection PyShadowingBuiltins
def prefab(
    cls=None,
    *,
    init=True,
    repr=True,
    eq=True,
    iter=False,
    match_args=True,
    kw_only=False,
    frozen=False,
    dict_method=False,
    recursive_repr=False,
):
    """
    Generate boilerplate code for dunder methods in a class.

    Use as a decorator.

    :param cls: Class to convert to a prefab
    :param init: generates __init__ if true or __prefab_init__ if false
    :param repr: generate __repr__
    :param eq: generate __eq__
    :param iter: generate __iter__
    :param match_args: generate __match_args__
    :param kw_only: make all attributes keyword only
    :param frozen: Prevent attribute values from being changed once defined
                   (This does not prevent the modification of mutable attributes such as lists)
    :param dict_method: Include an as_dict method for faster dictionary creation
    :param recursive_repr: Safely handle repr in case of recursion

    :return: class with __ methods defined
    """
    if not cls:
        # Called as () method to change defaults
        return lambda cls_: prefab(
            cls_,
            init=init,
            repr=repr,
            eq=eq,
            iter=iter,
            match_args=match_args,
            kw_only=kw_only,
            frozen=frozen,
            dict_method=dict_method,
            recursive_repr=recursive_repr,
        )
    else:
        return _make_prefab(
            cls,
            init=init,
            repr=repr,
            eq=eq,
            iter=iter,
            match_args=match_args,
            kw_only=kw_only,
            frozen=frozen,
            dict_method=dict_method,
            recursive_repr=recursive_repr,
        )


# noinspection PyShadowingBuiltins
def build_prefab(
    class_name,
    attributes,
    *,
    bases=(),
    class_dict=None,
    init=True,
    repr=True,
    eq=True,
    iter=False,
    match_args=True,
    kw_only=False,
    frozen=False,
    dict_method=False,
    recursive_repr=False,
    slots=False,
):
    """
    Dynamically construct a (dynamic) prefab.

    :param class_name: name of the resulting prefab class
    :param attributes: list of (name, attribute()) pairs to assign to the class
                       for construction
    :param bases: Base classes to inherit from
    :param class_dict: Other values to add to the class dictionary on creation
                       This is the 'dict' parameter from 'type'
    :param init: generates __init__ if true or __prefab_init__ if false
    :param repr: generate __repr__
    :param eq: generate __eq__
    :param iter: generate __iter__
    :param match_args: generate __match_args__
    :param kw_only: make all attributes keyword only
    :param frozen: Prevent attribute values from being changed once defined
                   (This does not prevent the modification of mutable attributes such as lists)
    :param dict_method: Include an as_dict method for faster dictionary creation
    :param recursive_repr: Safely handle repr in case of recursion
    :param slots: Make the resulting class slotted
    :return: class with __ methods defined
    """
    class_dict = {} if class_dict is None else class_dict.copy()

    class_annotations = {}
    class_slots = {}
    fields = {}

    for name, attrib in attributes:
        if isinstance(attrib, Attribute):
            fields[name] = attrib
        elif isinstance(attrib, Field):
            fields[name] = Attribute.from_field(attrib)
        else:
            fields[name] = Attribute(default=attrib)

        if attrib.type is not NOTHING:
            class_annotations[name] = attrib.type

        class_slots[name] = attrib.doc

    if slots:
        class_dict["__slots__"] = class_slots

    class_dict["__annotations__"] = class_annotations
    cls = type(class_name, bases, class_dict)

    gathered_fields = GatheredFields(fields, {})

    cls = _make_prefab(
        cls,
        init=init,
        repr=repr,
        eq=eq,
        iter=iter,
        match_args=match_args,
        kw_only=kw_only,
        frozen=frozen,
        dict_method=dict_method,
        recursive_repr=recursive_repr,
        gathered_fields=gathered_fields,
    )

    return cls


# Extra Functions
def is_prefab(o):
    """
    Identifier function, return True if an object is a prefab class *or* if
    it is an instance of a prefab class.

    The check works by looking for a PREFAB_FIELDS attribute.

    :param o: object for comparison
    :return: True/False
    """
    cls = o if isinstance(o, type) else type(o)
    return hasattr(cls, PREFAB_FIELDS)


def is_prefab_instance(o):
    """
    Identifier function, return True if an object is an instance of a prefab
    class.

    The check works by looking for a PREFAB_FIELDS attribute.

    :param o: object for comparison
    :return: True/False
    """
    return hasattr(type(o), PREFAB_FIELDS)


def as_dict(o):
    """
    Get the valid fields from a prefab respecting the serialize
    values of attributes

    :param o: instance of a prefab class
    :return: dictionary of {k: v} from fields
    """
    cls = type(o)
    if not hasattr(cls, PREFAB_FIELDS):
        raise TypeError(f"{o!r} should be a prefab instance, not {cls}")

    # Attempt to use the generated method if available
    try:
        return o.as_dict()
    except AttributeError:
        pass

    flds = get_attributes(cls)

    return {
        name: getattr(o, name)
        for name, attrib in flds.items()
        if attrib.serialize
    }

def replace(obj, /, **changes):
    if not is_prefab_instance(obj):
        raise TypeError("replace() should be called on prefab instances")
    return obj.__replace__(**changes)
