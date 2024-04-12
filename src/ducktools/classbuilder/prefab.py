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

import sys

from . import (
    INTERNALS_DICT, NOTHING,
    Field, MethodMaker, SlotFields,
    builder, fieldclass, get_internals, slot_gatherer
)

PREFAB_FIELDS = "PREFAB_FIELDS"
PREFAB_INIT_FUNC = "__prefab_init__"
PRE_INIT_FUNC = "__prefab_pre_init__"
POST_INIT_FUNC = "__prefab_post_init__"


# KW_ONLY sentinel 'type' to use to indicate all subsequent attributes are
# keyword only
# noinspection PyPep8Naming
class _KW_ONLY_TYPE:
    def __repr__(self):
        return "<KW_ONLY Sentinel Object>"


KW_ONLY = _KW_ONLY_TYPE()


class PrefabError(Exception):
    pass


def _is_classvar(hint):
    _typing = sys.modules.get("typing")
    if _typing:
        if (
            hint is _typing.ClassVar
            or getattr(hint, "__origin__", None) is _typing.ClassVar
        ):
            return True
        # String used as annotation
        elif isinstance(hint, str) and "ClassVar" in hint:
            return True
    return False


def get_attributes(cls):
    """
    Copy of get_fields, typed to return Attribute instead of Field.
    This is used in the prefab methods.

    :param cls: class built with _make_prefab
    :return: dict[str, Attribute] of all gathered attributes
    """
    return getattr(cls, INTERNALS_DICT)["fields"]


# Method Generators
def get_init_maker(*, init_name="__init__"):
    def __init__(cls: "type") -> "tuple[str, dict]":
        globs = {}
        internals = get_internals(cls)
        # Get the internals dictionary and prepare attributes
        attributes = internals["fields"]
        kw_only = internals["kw_only"]

        # Handle pre/post init first - post_init can change types for __init__
        # Get pre and post init arguments
        pre_init_args = []
        post_init_args = []
        post_init_annotations = {}

        for func_name, func_arglist in [
            (PRE_INIT_FUNC, pre_init_args),
            (POST_INIT_FUNC, post_init_args),
        ]:
            try:
                func = getattr(cls, func_name)
                func_code = func.__code__
            except AttributeError:
                pass
            else:
                argcount = func_code.co_argcount + func_code.co_kwonlyargcount

                # Identify if method is static, if so include first arg, otherwise skip
                is_static = type(cls.__dict__.get(func_name)) is staticmethod

                arglist = (
                    func_code.co_varnames[:argcount]
                    if is_static
                    else func_code.co_varnames[1:argcount]
                )

                func_arglist.extend(arglist)

                if func_name == POST_INIT_FUNC:
                    post_init_annotations.update(func.__annotations__)

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
            f"def {init_name}(self, {args}):\n"
            f"{pre_init_call}\n"
            f"{body}\n"
            f"{post_init_call}\n"
        )
        return code, globs

    return MethodMaker(init_name, __init__)


def get_repr_maker(*, recursion_safe=False):
    def __repr__(cls: "type") -> "tuple[str, dict]":
        attributes = get_attributes(cls)

        globs = {}

        will_eval = True
        valid_names = []
        for name, attrib in attributes.items():
            if attrib.repr and not attrib.exclude_field:
                valid_names.append(name)

            # If the init fields don't match the repr, or some fields are excluded
            # generate a repr that clearly will not evaluate
            if will_eval and (attrib.exclude_field or (attrib.init ^ attrib.repr)):
                will_eval = False

        content = ", ".join(
            f"{name}={{self.{name}!r}}"
            for name in valid_names
        )

        if recursion_safe:
            import reprlib
            globs["_recursive_repr"] = reprlib.recursive_repr()
            recursion_func = "@_recursive_repr\n"
        else:
            recursion_func = ""

        if will_eval:
            code = (
                f"{recursion_func}"
                f"def __repr__(self):\n"
                f"    return f'{{type(self).__qualname__}}({content})'\n"
            )
        else:
            if content:
                code = (
                    f"{recursion_func}"
                    f"def __repr__(self):\n"
                    f"    return f'<prefab {{type(self).__qualname__}}; {content}>'\n"
                )
            else:
                code = (
                    f"{recursion_func}"
                    f"def __repr__(self):\n"
                    f"    return f'<prefab {{type(self).__qualname__}}>'\n"
                )

        return code, globs

    return MethodMaker("__repr__", __repr__)


def get_eq_maker():
    def __eq__(cls: "type") -> "tuple[str, dict]":
        class_comparison = "self.__class__ is other.__class__"
        attribs = get_attributes(cls)
        field_names = [
            name
            for name, attrib in attribs.items()
            if attrib.compare and not attrib.exclude_field
        ]

        if field_names:
            selfvals = ",".join(f"self.{name}" for name in field_names)
            othervals = ",".join(f"other.{name}" for name in field_names)
            instance_comparison = f"({selfvals},) == ({othervals},)"
        else:
            instance_comparison = "True"

        code = (
            f"def __eq__(self, other):\n"
            f"    return {instance_comparison} if {class_comparison} else NotImplemented\n"
        )
        globs = {}

        return code, globs

    return MethodMaker("__eq__", __eq__)


def get_iter_maker():
    def __iter__(cls: "type") -> "tuple[str, dict]":
        fields = get_attributes(cls)

        valid_fields = (
            name for name, attrib in fields.items()
            if attrib.iter and not attrib.exclude_field
        )

        values = "\n".join(f"    yield self.{name}" for name in valid_fields)

        # if values is an empty string
        if not values:
            values = "    yield from ()"

        code = f"def __iter__(self):\n{values}"
        globs = {}
        return code, globs

    return MethodMaker("__iter__", __iter__)


def get_frozen_setattr_maker():
    def __setattr__(cls: "type") -> "tuple[str, dict]":
        globs = {}
        internals = get_internals(cls)
        field_names = internals["fields"].keys()

        # Make the fields set literal
        fields_delimited = ", ".join(f"{field!r}" for field in field_names)
        field_set = f"{{ {fields_delimited} }}"

        if internals["slotted"]:
            globs["__prefab_setattr_func"] = object.__setattr__
            setattr_method = "__prefab_setattr_func(self, name, value)"
        else:
            setattr_method = "self.__dict__[name] = value"

        body = (
            f"    if hasattr(self, name) or name not in {field_set}:\n"
            f'        raise TypeError(\n'
            f'            f"{{type(self).__name__!r}} object does not support "'
            f'            f"attribute assignment"\n'
            f'        )\n'
            f"    else:\n"
            f"        {setattr_method}\n"
        )
        code = f"def __setattr__(self, name, value):\n{body}"

        return code, globs

    # Pass the exception to exec
    return MethodMaker("__setattr__", __setattr__)


def get_frozen_delattr_maker():
    # noinspection PyUnusedLocal
    def __delattr__(cls: "type") -> "tuple[str, dict]":
        body = (
            '    raise TypeError(\n'
            '        f"{type(self).__name__!r} object "\n'
            '        f"does not support attribute deletion"\n'
            '    )\n'
        )
        code = f"def __delattr__(self, name):\n{body}"
        globs = {}
        return code, globs

    return MethodMaker("__delattr__", __delattr__)


def get_asdict_maker():
    def as_dict_gen(cls: "type") -> "tuple[str, dict]":
        fields = get_attributes(cls)

        vals = ", ".join(
            f"'{name}': self.{name}"
            for name, attrib in fields.items()
            if attrib.in_dict and not attrib.exclude_field
        )
        out_dict = f"{{{vals}}}"
        code = f"def as_dict(self): return {out_dict}"

        globs = {}
        return code, globs
    return MethodMaker("as_dict", as_dict_gen)


init_desc = get_init_maker()
prefab_init_desc = get_init_maker(init_name=PREFAB_INIT_FUNC)
repr_desc = get_repr_maker()
recursive_repr_desc = get_repr_maker(recursion_safe=True)
eq_desc = get_eq_maker()
iter_desc = get_iter_maker()
frozen_setattr_desc = get_frozen_setattr_maker()
frozen_delattr_desc = get_frozen_delattr_maker()
asdict_desc = get_asdict_maker()


# Updated field with additional attributes
@fieldclass
class Attribute(Field):
    __slots__ = SlotFields(
        init=True,
        repr=True,
        compare=True,
        iter=True,
        kw_only=False,
        in_dict=True,
        exclude_field=False,
    )

    def validate_field(self):
        super().validate_field()
        if self.kw_only and not self.init:
            raise PrefabError(
                "Attribute cannot be keyword only if it is not in init."
            )


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
    in_dict=True,
    exclude_field=False,
    doc=None,
    type=NOTHING,
):
    """
    Get an object to define a prefab Attribute

    :param default: Default value for this attribute
    :param default_factory: 0 argument callable to give a default value
                            (for otherwise mutable defaults, eg: list)
    :param init: Include this attribute in the __init__ parameters
    :param repr: Include this attribute in the class __repr__
    :param compare: Include this attribute in the class __eq__
    :param iter: Include this attribute in the class __iter__ if generated
    :param kw_only: Make this argument keyword only in init
    :param in_dict: Include this attribute in methods that serialise to dict
    :param exclude_field: Exclude this field from all magic method generation
                          apart from __init__ signature
                          and do not include it in PREFAB_FIELDS
                          Must be assigned in __prefab_post_init__
    :param doc: Parameter documentation for slotted classes
    :param type: Type of this attribute (for slotted classes)

    :return: Attribute generated with these parameters.
    """
    return Attribute(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        compare=compare,
        iter=iter,
        kw_only=kw_only,
        in_dict=in_dict,
        exclude_field=exclude_field,
        doc=doc,
        type=type,
    )


# Gatherer for classes built on attributes or annotations
def attribute_gatherer(cls):
    cls_annotations = cls.__dict__.get("__annotations__", {})
    cls_annotation_names = cls_annotations.keys()

    cls_slots = cls.__dict__.get("__slots__", {})

    cls_attributes = {
        k: v for k, v in vars(cls).items() if isinstance(v, Attribute)
    }

    cls_attribute_names = cls_attributes.keys()

    if set(cls_annotation_names).issuperset(set(cls_attribute_names)):
        # replace the classes' attributes dict with one with the correct
        # order from the annotations.
        kw_flag = False
        new_attributes = {}
        for name, value in cls_annotations.items():
            # Ignore ClassVar hints
            if _is_classvar(value):
                continue

            # Look for the KW_ONLY annotation
            if value is KW_ONLY or value == "KW_ONLY":
                if kw_flag:
                    raise PrefabError(
                        "Class can not be defined as keyword only twice"
                    )
                kw_flag = True
            else:
                # Copy attributes that are already defined to the new dict
                # generate Attribute() values for those that are not defined.

                # If a field name is also declared in slots it can't have a real
                # default value and the attr will be the slot descriptor.
                if hasattr(cls, name) and name not in cls_slots:
                    if name in cls_attribute_names:
                        attrib = cls_attributes[name]
                    else:
                        attribute_default = getattr(cls, name)
                        attrib = attribute(default=attribute_default)

                    # Clear the attribute from the class after it has been used
                    # in the definition.
                    delattr(cls, name)
                else:
                    attrib = attribute()

                if kw_flag:
                    attrib.kw_only = True

                attrib.type = cls_annotations[name]
                new_attributes[name] = attrib

        cls_attributes = new_attributes
    else:
        for name, attrib in cls_attributes.items():
            delattr(cls, name)

            # Some items can still be annotated.
            try:
                attrib.type = cls_annotations[name]
            except KeyError:
                pass

    return cls_attributes


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
    :return: class with __ methods defined
    """
    cls_dict = cls.__dict__

    if INTERNALS_DICT in cls_dict:
        raise PrefabError(
            f"Decorated class {cls.__name__!r} "
            f"has already been processed as a Prefab."
        )

    slots = cls_dict.get("__slots__")
    if isinstance(slots, SlotFields):
        gatherer = slot_gatherer
        slotted = True
    else:
        gatherer = attribute_gatherer
        slotted = False

    methods = set()

    if init and "__init__" not in cls_dict:
        methods.add(init_desc)
    else:
        methods.add(prefab_init_desc)

    if repr and "__repr__" not in cls_dict:
        if recursive_repr:
            methods.add(recursive_repr_desc)
        else:
            methods.add(repr_desc)
    if eq and "__eq__" not in cls_dict:
        methods.add(eq_desc)
    if iter and "__iter__" not in cls_dict:
        methods.add(iter_desc)
    if frozen:
        methods.add(frozen_setattr_desc)
        methods.add(frozen_delattr_desc)
    if dict_method:
        methods.add(asdict_desc)

    cls = builder(
        cls,
        gatherer=gatherer,
        methods=methods,
    )

    # Add fields not covered by builder
    internals = get_internals(cls)
    internals["slotted"] = slotted
    internals["kw_only"] = kw_only
    fields = internals["fields"]
    local_fields = internals["local_fields"]

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
    valid_args = []
    for name, attrib in fields.items():
        # slot_gather and parent classes may use Fields
        # prefabs require Attributes, so convert.
        if not isinstance(attrib, Attribute):
            attrib = Attribute.from_field(attrib)
            fields[name] = attrib
            if name in local_fields:
                local_fields[name] = attrib

        # Excluded fields *MUST* be forwarded to post_init
        if attrib.exclude_field:
            if name not in post_init_args:
                raise PrefabError(
                    f"{name!r} is an excluded attribute but is not passed to post_init"
                )
        else:
            valid_args.append(name)

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
    :return: class with __ methods defined
    """
    class_dict = {} if class_dict is None else class_dict
    cls = type(class_name, bases, class_dict)
    for name, attrib in attributes:
        setattr(cls, name, attrib)

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
    Get the valid fields from a prefab respecting the in_dict
    values of attributes

    :param o: instance of a prefab class
    :return: dictionary of {k: v} from fields
    """
    # Attempt to use the generated method if available
    try:
        return o.as_dict()
    except AttributeError:
        pass

    cls = type(o)
    try:
        flds = get_attributes(cls)
    except AttributeError:
        raise TypeError(f"inst should be a prefab instance, not {cls}")

    return {
        name: getattr(o, name)
        for name, attrib in flds.items()
        if attrib.in_dict and not attrib.exclude_field
    }
