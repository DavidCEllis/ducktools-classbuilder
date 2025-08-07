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

# In this module there are some internal bits of circular logic.
#
# 'Field' needs to exist in order to be used in gatherers, but is itself a
# partially constructed class. These constructed attributes are placed on
# 'Field' post construction.
#
# The 'SlotMakerMeta' metaclass generates 'Field' instances to go in __slots__
# but is also the metaclass used to construct 'Field'.
# Field itself sidesteps this by defining __slots__ to avoid that branch.

import os

from .annotations import get_ns_annotations, is_classvar
from ._version import __version__, __version_tuple__  # noqa: F401

# Change this name if you make heavy modifications
INTERNALS_DICT = "__classbuilder_internals__"
META_GATHERER_NAME = "_meta_gatherer"
GATHERED_DATA = "__classbuilder_gathered_fields__"

# If testing, make Field classes frozen to make sure attributes are not
# overwritten. When running this is a performance penalty so it is not required.
_UNDER_TESTING = os.environ.get("PYTEST_VERSION") is not None

# Obtain types the same way types.py does in pypy
# See: https://github.com/pypy/pypy/blob/19d9fa6be11165116dd0839b9144d969ab426ae7/lib-python/3/types.py#L61-L73
class _C: __slots__ = 's'  # noqa
_MemberDescriptorType = type(_C.s)  # type: ignore
_MappingProxyType = type(type.__dict__)
del _C


def get_fields(cls, *, local=False):
    """
    Utility function to gather the fields dictionary
    from the class internals.

    :param cls: generated class
    :param local: get only fields that were not inherited
    :return: dictionary of keys and Field attribute info
    """
    key = "local_fields" if local else "fields"
    return getattr(cls, INTERNALS_DICT)[key]


def get_flags(cls):
    """
    Utility function to gather the flags dictionary
    from the class internals.

    :param cls: generated class
    :return: dictionary of keys and flag values
    """
    return getattr(cls, INTERNALS_DICT)["flags"]


def get_methods(cls):
    """
    Utility function to gather the set of methods
    from the class internals.

    :param cls: generated class
    :return: dict of generated methods attached to the class by name
    """
    return getattr(cls, INTERNALS_DICT)["methods"]


def _get_inst_fields(inst):
    # This is an internal helper for constructing new
    # 'Field' instances from existing ones.
    return {
        k: getattr(inst, k)
        for k in get_fields(type(inst))
    }


# As 'None' can be a meaningful value we need a sentinel value
# to use to show no value has been provided.
class _NothingType:
    def __init__(self, custom=None):
        self.custom = custom
    def __repr__(self):
        if self.custom:
            return f"<{self.custom} NOTHING OBJECT>"
        return "<NOTHING OBJECT>"


NOTHING = _NothingType()
FIELD_NOTHING = _NothingType("FIELD")


# KW_ONLY sentinel 'type' to use to indicate all subsequent attributes are
# keyword only
# noinspection PyPep8Naming
class _KW_ONLY_META(type):
    def __repr__(self):
        return "<KW_ONLY Sentinel>"


class KW_ONLY(metaclass=_KW_ONLY_META):
    """
    Sentinel Class to indicate that variables declared after
    this sentinel are to be converted to KW_ONLY arguments.
    """


class GeneratedCode:
    """
    This class provides a return value for the generated output from source code
    generators.
    """
    __slots__ = ("source_code", "globs")

    def __init__(self, source_code, globs):
        self.source_code = source_code
        self.globs = globs

    def __repr__(self):
        first_source_line = self.source_code.split("\n")[0]
        return f"GeneratorOutput(source_code='{first_source_line} ...', globs={self.globs!r})"

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.source_code, self.globs) == (other.source_code, other.globs)
        return NotImplemented


class MethodMaker:
    """
    The descriptor class to place where methods should be generated.
    This delays the actual generation and `exec` until the method is needed.

    This is used to convert a code generator that returns code and a globals
    dictionary into a descriptor to assign on a generated class.
    """
    def __init__(self, funcname, code_generator):
        """
        :param funcname: name of the generated function eg `__init__`
        :param code_generator: code generator function to operate on a class.
        """
        self.funcname = funcname
        self.code_generator = code_generator

    def __repr__(self):
        return f"<MethodMaker for {self.funcname!r} method>"

    def __get__(self, inst, cls):
        local_vars = {}

        # This can be called via super().funcname(...) in which case the class
        # may not be the correct one. If this is the correct class
        # it should have this descriptor in the class dict under
        # the correct funcname.
        # Otherwise is should be found in the MRO of the class.
        if cls.__dict__.get(self.funcname) is self:
            gen_cls = cls
        else:
            for c in cls.__mro__[1:]:  # skip 'cls' as special cased
                if c.__dict__.get(self.funcname) is self:
                    gen_cls = c
                    break
            else:  # pragma: no cover
                # This should only be reached if called with incorrect arguments
                # manually
                raise AttributeError(
                    f"Could not find {self!r} in class {cls.__name__!r} MRO."
                )

        gen = self.code_generator(gen_cls, self.funcname)
        exec(gen.source_code, gen.globs, local_vars)
        method = local_vars.get(self.funcname)

        try:
            method.__qualname__ = f"{gen_cls.__qualname__}.{self.funcname}"
        except AttributeError:
            # This might be a property or some other special
            # descriptor. Don't try to rename.
            pass

        # Replace this descriptor on the class with the generated function
        setattr(gen_cls, self.funcname, method)

        # Use 'get' to return the generated function as a bound method
        # instead of as a regular function for first usage.
        return method.__get__(inst, cls)


class _SignatureMaker:
    # 'inspect.signature' calls the `__get__` method of the `__init__` methodmaker with
    # the wrong arguments.
    # Instead of __get__(None, cls) or __get__(inst, type(inst))
    # it uses __get__(cls, type(cls)).
    #
    # If this is done before `__init__` has been generated then
    # help(cls) will fail along with inspect.signature(cls)
    # This signature maker descriptor is placed to override __signature__ and force
    # the `__init__` signature to be generated first if the signature is requested.
    def __get__(self, instance, cls=None):
        if cls is None:
            cls = type(instance)

        # force generation of `__init__` function
        _ = cls.__init__

        if instance is None:
            raise AttributeError(
                f"type object {cls.__name__!r} "
                "has no attribute '__signature__'"
            )
        else:
            raise AttributeError(
                f"{cls.__name__!r} object"
                "has no attribute '__signature__'"
            )


signature_maker = _SignatureMaker()


def get_init_generator(null=NOTHING, extra_code=None):
    def cls_init_maker(cls, funcname="__init__"):
        fields = get_fields(cls)
        flags = get_flags(cls)

        arglist = []
        kw_only_arglist = []
        assignments = []
        globs = {}

        kw_only_flag = flags.get("kw_only", False)

        for k, v in fields.items():
            if v.init:
                if v.default is not null:
                    globs[f"_{k}_default"] = v.default
                    arg = f"{k}=_{k}_default"
                    assignment = f"self.{k} = {k}"
                elif v.default_factory is not null:
                    globs[f"_{k}_factory"] = v.default_factory
                    arg = f"{k}=None"
                    assignment = f"self.{k} = _{k}_factory() if {k} is None else {k}"
                else:
                    arg = f"{k}"
                    assignment = f"self.{k} = {k}"

                if kw_only_flag or v.kw_only:
                    kw_only_arglist.append(arg)
                else:
                    arglist.append(arg)

                assignments.append(assignment)
            else:
                if v.default is not null:
                    globs[f"_{k}_default"] = v.default
                    assignment = f"self.{k} = _{k}_default"
                    assignments.append(assignment)
                elif v.default_factory is not null:
                    globs[f"_{k}_factory"] = v.default_factory
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

        assigns = "\n    ".join(assignments) if assignments else "pass\n"
        code = (
            f"def {funcname}(self, {args}):\n"
            f"    {assigns}\n"
        )
        # Handle additional function calls
        # Used for validate_field on fieldclasses
        if extra_code:
            for line in extra_code:
                code += f"    {line}\n"

        return GeneratedCode(code, globs)

    return cls_init_maker


init_generator = get_init_generator()


def get_repr_generator(recursion_safe=False, eval_safe=False):
    """

    :param recursion_safe: use reprlib.recursive_repr
    :param eval_safe: if the repr is known not to eval correctly,
                      generate a repr which will intentionally
                      not evaluate.
    :return:
    """
    def cls_repr_generator(cls, funcname="__repr__"):
        fields = get_fields(cls)

        globs = {}
        will_eval = True
        valid_names = []

        for name, fld in fields.items():
            if fld.repr:
                valid_names.append(name)

            if will_eval and (fld.init ^ fld.repr):
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

        if eval_safe and will_eval is False:
            if content:
                code = (
                    f"{recursion_func}"
                    f"def {funcname}(self):\n"
                    f"    return f'<generated class {{type(self).__qualname__}}; {content}>'\n"
                )
            else:
                code = (
                    f"{recursion_func}"
                    f"def {funcname}(self):\n"
                    f"    return f'<generated class {{type(self).__qualname__}}>'\n"
                )
        else:
            code = (
                f"{recursion_func}"
                f"def {funcname}(self):\n"
                f"    return f'{{type(self).__qualname__}}({content})'\n"
            )

        return GeneratedCode(code, globs)
    return cls_repr_generator


repr_generator = get_repr_generator()


def eq_generator(cls, funcname="__eq__"):
    class_comparison = "self.__class__ is other.__class__"
    field_names = [
        name
        for name, attrib in get_fields(cls).items()
        if attrib.compare
    ]

    if field_names:
        instance_comparison = "\n        and ".join(
            f"self.{name} == other.{name}" for name in field_names
        )
    else:
        instance_comparison = "True"

    code = (
        f"def {funcname}(self, other):\n"
        f"    return (\n"
        f"        {instance_comparison}\n"
        f"    ) if {class_comparison} else NotImplemented\n"
    )
    globs = {}

    return GeneratedCode(code, globs)


def replace_generator(cls, funcname="__replace__"):
    # Generate the replace method for built classes
    # unlike the dataclasses implementation this is generated
    attribs = get_fields(cls)

    # This is essentially the as_dict generator for prefabs
    # except based on attrib.init instead of .serialize
    vals = ", ".join(
        f"'{name}': self.{name}"
        for name, attrib in attribs.items()
        if attrib.init
    )
    init_dict = f"{{{vals}}}"

    code = (
        f"def {funcname}(self, /, **changes):\n"
        f"    new_kwargs = {init_dict}\n"
        f"    for name, value in changes.items():\n"
        f"        if name not in new_kwargs:\n"
        f"            raise TypeError(\n"
        f"                f\"{{name!r}} is not a valid replacable \"\n"
        f"                f\"field on {{self.__class__.__name__!r}}\"\n"
        f"            )\n"
        f"        new_kwargs[name] = value\n"
        f"    return self.__class__(**new_kwargs)\n"
    )
    globs = {}
    return GeneratedCode(code, globs)


def frozen_setattr_generator(cls, funcname="__setattr__"):
    globs = {}
    field_names = set(get_fields(cls))
    flags = get_flags(cls)

    globs["__field_names"] = field_names

    # Better to be safe and use the method that works in both cases
    # if somehow slotted has not been set.
    if flags.get("slotted", True):
        globs["__setattr_func"] = object.__setattr__
        setattr_method = "__setattr_func(self, name, value)"
        hasattr_check = "hasattr(self, name)"
    else:
        setattr_method = "self.__dict__[name] = value"
        hasattr_check = "name in self.__dict__"

    body = (
        f"    if {hasattr_check} or name not in __field_names:\n"
        f'        raise TypeError(\n'
        f'            f"{{type(self).__name__!r}} object does not support "'
        f'            f"attribute assignment"\n'
        f'        )\n'
        f"    else:\n"
        f"        {setattr_method}\n"
    )
    code = f"def {funcname}(self, name, value):\n{body}"

    return GeneratedCode(code, globs)


def frozen_delattr_generator(cls, funcname="__delattr__"):
    body = (
        '    raise TypeError(\n'
        '        f"{type(self).__name__!r} object "\n'
        '        f"does not support attribute deletion"\n'
        '    )\n'
    )
    code = f"def {funcname}(self, name):\n{body}"
    globs = {}
    return GeneratedCode(code, globs)


# As only the __get__ method refers to the class we can use the same
# Descriptor instances for every class.
init_maker = MethodMaker("__init__", init_generator)
repr_maker = MethodMaker("__repr__", repr_generator)
eq_maker = MethodMaker("__eq__", eq_generator)
replace_maker = MethodMaker("__replace__", replace_generator)
frozen_setattr_maker = MethodMaker("__setattr__", frozen_setattr_generator)
frozen_delattr_maker = MethodMaker("__delattr__", frozen_delattr_generator)
default_methods = frozenset({init_maker, repr_maker, eq_maker})

# Special `__init__` maker for 'Field' subclasses - needs its own NOTHING option
_field_init_maker = MethodMaker(
    funcname="__init__",
    code_generator=get_init_generator(
        null=FIELD_NOTHING,
        extra_code=["self.validate_field()"],
    )
)


def builder(cls=None, /, *, gatherer, methods, flags=None, fix_signature=True):
    """
    The main builder for class generation

    :param cls: Class to be analysed and have methods generated
    :param gatherer: Function to gather field information
    :type gatherer: Callable[[type], tuple[dict[str, Field], dict[str, Any]]]
    :param methods: MethodMakers to add to the class
    :type methods: set[MethodMaker]
    :param flags: additional flags to store in the internals dictionary
                  for use by method generators.
    :type flags: None | dict[str, bool]
    :param fix_signature: Add a __signature__ attribute to work-around an issue with
                          inspect.signature incorrectly handling __init__ descriptors.
    :type fix_signature: bool
    :return: The modified class (the class itself is modified, but this is expected).
    """
    # Handle `None` to make wrapping with a decorator easier.
    if cls is None:
        return lambda cls_: builder(
            cls_,
            gatherer=gatherer,
            methods=methods,
            flags=flags,
        )

    internals = {}
    setattr(cls, INTERNALS_DICT, internals)

    cls_fields, modifications = gatherer(cls)

    for name, value in modifications.items():
        if value is NOTHING:
            delattr(cls, name)
        else:
            setattr(cls, name, value)

    internals["local_fields"] = cls_fields

    mro = cls.__mro__[:-1]  # skip 'object' base class
    if mro == (cls,):  # special case of no inheritance.
        fields = cls_fields.copy()
    else:
        fields = {}
        for c in reversed(mro):
            try:
                fields.update(get_fields(c, local=True))
            except AttributeError:
                pass

    internals["fields"] = fields
    internals["flags"] = flags if flags is not None else {}

    # Assign all of the method generators
    internal_methods = {}
    for method in methods:
        setattr(cls, method.funcname, method)
        internal_methods[method.funcname] = method

    internals["methods"] = _MappingProxyType(internal_methods)

    # Fix for inspect.signature(cls)
    if fix_signature:
        setattr(cls, "__signature__", signature_maker)

    return cls


# Slot gathering tools
# Subclass of dict to be identifiable by isinstance checks
# For anything more complicated this could be made into a Mapping
class SlotFields(dict):
    """
    A plain dict subclass.

    For declaring slotfields there are no additional features required
    other than recognising that this is intended to be used as a class
    generating dict and isn't a regular dictionary that ended up in
    `__slots__`.

    This should be replaced on `__slots__` after fields have been gathered.
    """
    def __repr__(self):
        return f"SlotFields({super().__repr__()})"


# Tool to convert annotations to slots as a metaclass
class SlotMakerMeta(type):
    """
    Metaclass to convert annotations or Field(...) attributes to slots.

    Will not convert `ClassVar` hinted values.
    """
    def __new__(cls, name, bases, ns, slots=True, gatherer=None, **kwargs):
        # This should only run if slots=True is declared
        # and __slots__ have not already been defined
        if slots and "__slots__" not in ns:
            # Check if a different gatherer has been set in any base classes
            # Default to unified gatherer
            if gatherer is None:
                gatherer = ns.get(META_GATHERER_NAME, None)
                if not gatherer:
                    for base in bases:
                        if g := getattr(base, META_GATHERER_NAME, None):
                            gatherer = g
                            break

                if not gatherer:
                    gatherer = unified_gatherer

            # Set the gatherer in the namespace
            ns[META_GATHERER_NAME] = gatherer

            # Obtain slots from annotations or attributes
            cls_fields, cls_modifications = gatherer(ns)
            for k, v in cls_modifications.items():
                if v is NOTHING:
                    ns.pop(k)
                else:
                    ns[k] = v

            slots = {}
            fields = {}

            for k, v in cls_fields.items():
                slots[k] = v.doc
                if k not in {"__weakref__", "__dict__"}:
                    fields[k] = v

            # Place slots *after* everything else to be safe
            ns["__slots__"] = slots

            # Place pre-gathered field data - modifications are already applied
            modifications = {}
            ns[GATHERED_DATA] = fields, modifications

        else:
            if gatherer is not None:
                ns[META_GATHERER_NAME] = gatherer

        new_cls = super().__new__(cls, name, bases, ns, **kwargs)

        return new_cls


# This class is set up before fields as it will be used to generate the Fields
# for Field itself so Field can have generated __eq__, __repr__ and other methods
class GatheredFields:
    """
    Helper class to store gathered field data
    """
    __slots__ = ("fields", "modifications")

    def __init__(self, fields, modifications):
        self.fields = fields
        self.modifications = modifications

    def __eq__(self, other):
        if type(self) is type(other):
            return self.fields == other.fields and self.modifications == other.modifications

    def __repr__(self):
        return f"{type(self).__name__}(fields={self.fields!r}, modifications={self.modifications!r})"

    def __call__(self, cls_dict):
        # cls_dict will be provided, but isn't needed
        return self.fields, self.modifications


# The Field class can finally be defined.
# The __init__ method has to be written manually so Fields can be created
# However after this, the other methods can be generated.
class Field(metaclass=SlotMakerMeta):
    """
    A basic class to handle the assignment of defaults/factories with
    some metadata.

    Intended to be extendable by subclasses for additional features.

    Note: When run under `pytest`, Field instances are Frozen.

    When subclassing, passing `frozen=True` will make your subclass frozen.

    :param default: Standard default value to be used for attributes with this field.
    :param default_factory: A zero-argument function to be called to generate a
                            default value, useful for mutable obects like lists.
    :param type: The type of the attribute to be assigned by this field.
    :param doc: The documentation for the attribute that appears when calling
                help(...) on the class. (Only in slotted classes).
    :param init: Include in the class __init__ parameters.
    :param repr: Include in the class __repr__.
    :param compare: Include in the class __eq__.
    :param kw_only: Make this a keyword only parameter in __init__.
    """

    # Plain slots are required as part of bootstrapping
    # This prevents SlotMakerMeta from trying to generate 'Field's
    __slots__ = (
        "default",
        "default_factory",
        "type",
        "doc",
        "init",
        "repr",
        "compare",
        "kw_only",
    )

    # noinspection PyShadowingBuiltins
    def __init__(
        self,
        *,
        default=NOTHING,
        default_factory=NOTHING,
        type=NOTHING,
        doc=None,
        init=True,
        repr=True,
        compare=True,
        kw_only=False,
    ):
        # The init function for 'Field' cannot be generated
        # as 'Field' needs to exist first.
        # repr and comparison functions are generated as these
        # do not need to exist to create initial Fields.

        self.default = default
        self.default_factory = default_factory
        self.type = type
        self.doc = doc

        self.init = init
        self.repr = repr
        self.compare = compare
        self.kw_only = kw_only

        self.validate_field()

    def __init_subclass__(cls, frozen=False):
        # Subclasses of Field can be created as if they are dataclasses
        field_methods = {_field_init_maker, repr_maker, eq_maker}
        if frozen or _UNDER_TESTING:
            field_methods.update({frozen_setattr_maker, frozen_delattr_maker})

        builder(
            cls,
            gatherer=unified_gatherer,
            methods=field_methods,
            flags={"slotted": True, "kw_only": True}
        )

    def validate_field(self):
        cls_name = self.__class__.__name__
        if type(self.default) is not _NothingType and type(self.default_factory) is not _NothingType:
            raise AttributeError(
                f"{cls_name} cannot define both a default value and a default factory."
            )

    @classmethod
    def from_field(cls, fld, /, **kwargs):
        """
        Create an instance of field or subclass from another field.

        This is intended to be used to convert a base
        Field into a subclass.

        :param fld: field class to convert
        :param kwargs: Additional keyword arguments for subclasses
        :return: new field subclass instance
        """
        argument_dict = {**_get_inst_fields(fld), **kwargs}

        return cls(**argument_dict)


def _build_field():
    # Complete the construction of the Field class
    field_docs = {
        "default": "Standard default value to be used for attributes with this field.",
        "default_factory":
            "A zero-argument function to be called to generate a default value, "
            "useful for mutable obects like lists.",
        "type": "The type of the attribute to be assigned by this field.",
        "doc":
            "The documentation for the attribute that appears when calling "
            "help(...) on the class. (Only in slotted classes).",
        "init": "Include this attribute in the class __init__ parameters.",
        "repr": "Include this attribute in the class __repr__",
        "compare": "Include this attribute in the class __eq__ method",
        "kw_only": "Make this a keyword only parameter in __init__",
    }

    fields = {
        "default": Field(default=NOTHING, doc=field_docs["default"]),
        "default_factory": Field(default=NOTHING, doc=field_docs["default_factory"]),
        "type": Field(default=NOTHING, doc=field_docs["type"]),
        "doc": Field(default=None, doc=field_docs["doc"]),
        "init": Field(default=True, doc=field_docs["init"]),
        "repr": Field(default=True, doc=field_docs["repr"]),
        "compare": Field(default=True, doc=field_docs["compare"]),
        "kw_only": Field(default=False, doc=field_docs["kw_only"])
    }
    modifications = {"__slots__": field_docs}

    field_methods = {repr_maker, eq_maker}
    if _UNDER_TESTING:
        field_methods.update({frozen_setattr_maker, frozen_delattr_maker})

    builder(
        Field,
        gatherer=GatheredFields(fields, modifications),
        methods=field_methods,
        flags={"slotted": True, "kw_only": True},
    )


_build_field()
del _build_field


def pre_gathered_gatherer(cls_or_ns):
    """
    Retrieve fields previously gathered by SlotMakerMeta

    :param cls_or_ns: Class to gather field information from (or class namespace)
    :return: dict of field_name: Field(...) and modifications to be performed by the builder
    """
    if isinstance(cls_or_ns, (_MappingProxyType, dict)):
        cls_dict = cls_or_ns
    else:
        cls_dict = cls_or_ns.__dict__

    return cls_dict[GATHERED_DATA]


def make_slot_gatherer(field_type=Field):
    """
    Create a new annotation gatherer that will work with `Field` instances
    of the creators definition.

    :param field_type: The `Field` classes to be used when gathering fields
    :return: A slot gatherer that will check for and generate Fields of
             the type field_type.
    """
    def field_slot_gatherer(cls_or_ns):
        """
        Gather field information for class generation based on __slots__

        :param cls_or_ns: Class to gather field information from (or class namespace)
        :return: dict of field_name: Field(...) and modifications to be performed by the builder
        """
        if isinstance(cls_or_ns, (_MappingProxyType, dict)):
            cls_dict = cls_or_ns
        else:
            cls_dict = cls_or_ns.__dict__

        try:
            cls_slots = cls_dict["__slots__"]
        except KeyError:
            raise AttributeError(
                "__slots__ must be defined as an instance of SlotFields "
                "in order to generate a slotclass"
            )

        if not isinstance(cls_slots, SlotFields):
            raise TypeError(
                "__slots__ must be an instance of SlotFields "
                "in order to generate a slotclass"
            )

        cls_fields = {}
        slot_replacement = {}

        for k, v in cls_slots.items():
            # Special case __dict__ and __weakref__
            # They should be included in the final `__slots__`
            # But ignored as a value.
            if k in {"__dict__", "__weakref__"}:
                slot_replacement[k] = None
                continue

            if isinstance(v, field_type):
                attrib = v
            else:
                # Plain values treated as defaults
                attrib = field_type(default=v)

            slot_replacement[k] = attrib.doc
            cls_fields[k] = attrib

        # Send the modifications to the builder for what should be changed
        # On the class.
        # In this case, slots with documentation and new annotations.
        modifications = {
            "__slots__": slot_replacement,
        }

        return cls_fields, modifications

    return field_slot_gatherer


def make_annotation_gatherer(
    field_type=Field,
    leave_default_values=False,
):
    """
    Create a new annotation gatherer that will work with `Field` instances
    of the creators definition.

    :param field_type: The `Field` classes to be used when gathering fields
    :param leave_default_values: Set to True if the gatherer should leave
                                 default values in place as class variables.
    :return: An annotation gatherer with these settings.
    """
    def field_annotation_gatherer(cls_or_ns):
        if isinstance(cls_or_ns, (_MappingProxyType, dict)):
            cls_dict = cls_or_ns
        else:
            cls_dict = cls_or_ns.__dict__

        # This should really be dict[str, field_type] but static analysis
        # doesn't understand this.
        cls_fields: dict[str, Field] = {}
        modifications = {}

        cls_annotations = get_ns_annotations(cls_dict)

        kw_flag = False

        for k, v in cls_annotations.items():
            # Ignore ClassVar
            if is_classvar(v):
                continue

            if v is KW_ONLY or (isinstance(v, str) and v == "KW_ONLY"):
                if kw_flag:
                    raise SyntaxError("KW_ONLY sentinel may only appear once.")
                kw_flag = True
                continue

            attrib = cls_dict.get(k, NOTHING)

            if attrib is not NOTHING:
                if isinstance(attrib, field_type):
                    kw_only = attrib.kw_only or kw_flag

                    attrib = field_type.from_field(attrib, type=v, kw_only=kw_only)

                    if attrib.default is not NOTHING and leave_default_values:
                        modifications[k] = attrib.default
                    else:
                        # NOTHING sentinel indicates a value should be removed
                        modifications[k] = NOTHING
                elif not isinstance(attrib, _MemberDescriptorType):
                    attrib = field_type(default=attrib, type=v, kw_only=kw_flag)
                    if not leave_default_values:
                        modifications[k] = NOTHING
                else:
                    attrib = field_type(type=v, kw_only=kw_flag)
            else:
                attrib = field_type(type=v, kw_only=kw_flag)

            cls_fields[k] = attrib

        return cls_fields, modifications

    return field_annotation_gatherer


def make_field_gatherer(
    field_type=Field,
    leave_default_values=False,
    assign_types=True,
):
    def field_attribute_gatherer(cls_or_ns):
        if isinstance(cls_or_ns, (_MappingProxyType, dict)):
            cls_dict = cls_or_ns
        else:
            cls_dict = cls_or_ns.__dict__

        cls_attributes = {
            k: v
            for k, v in cls_dict.items()
            if isinstance(v, field_type)
        }

        if assign_types:
            cls_annotations = get_ns_annotations(cls_dict)
        else:
            cls_annotations = {}

        cls_modifications = {}

        for name in cls_attributes.keys():
            attrib = cls_attributes[name]
            if leave_default_values:
                cls_modifications[name] = attrib.default
            else:
                cls_modifications[name] = NOTHING

            if assign_types and (anno := cls_annotations.get(name, NOTHING)) is not NOTHING:
                cls_attributes[name] = field_type.from_field(attrib, type=anno)

        return cls_attributes, cls_modifications
    return field_attribute_gatherer


def make_unified_gatherer(
    field_type=Field,
    leave_default_values=False,
    ignore_annotations=False,
):
    """
    Create a gatherer that will work via first slots, then
    Field(...) class attributes and finally annotations if
    no unannotated Field(...) attributes are present.

    :param field_type: The field class to use for gathering
    :param leave_default_values: leave default values in place
    :param ignore_annotations: don't attempt to read annotations
    :return: gatherer function
    """
    slot_g = make_slot_gatherer(field_type)
    anno_g = make_annotation_gatherer(field_type, leave_default_values)
    attrib_g = make_field_gatherer(field_type, leave_default_values)

    def field_unified_gatherer(cls_or_ns):
        if isinstance(cls_or_ns, (_MappingProxyType, dict)):
            cls_dict = cls_or_ns
        else:
            cls_dict = cls_or_ns.__dict__

        cls_gathered = cls_dict.get(GATHERED_DATA)
        if cls_gathered:
            return pre_gathered_gatherer(cls_dict)

        cls_slots = cls_dict.get("__slots__")

        if isinstance(cls_slots, SlotFields):
            return slot_g(cls_dict)

        if ignore_annotations:
            return attrib_g(cls_dict)
        else:
            # To choose between annotation and attribute gatherers
            # compare sets of names.
            # Don't bother evaluating string annotations, as we only need names
            cls_annotations = get_ns_annotations(cls_dict)
            cls_attributes = {
                k: v for k, v in cls_dict.items() if isinstance(v, field_type)
            }

            cls_annotation_names = cls_annotations.keys()
            cls_attribute_names = cls_attributes.keys()

            if set(cls_annotation_names).issuperset(set(cls_attribute_names)):
                # All `Field` values have annotations, so use annotation gatherer
                return anno_g(cls_dict)

            return attrib_g(cls_dict)

    return field_unified_gatherer


slot_gatherer = make_slot_gatherer()
annotation_gatherer = make_annotation_gatherer()

# The unified gatherer used for slot classes must remove default
# values for slots to work correctly.
unified_gatherer = make_unified_gatherer()


def check_argument_order(cls):
    """
    Raise a SyntaxError if the argument order will be invalid for a generated
    `__init__` function.

    :param cls: class being built
    """
    fields = get_fields(cls)
    used_default = False
    for k, v in fields.items():
        if v.kw_only or (not v.init):
            continue

        if v.default is NOTHING and v.default_factory is NOTHING:
            if used_default:
                raise SyntaxError(
                    f"non-default argument {k!r} follows default argument"
                )
        else:
            used_default = True


# Class Decorators
def slotclass(cls=None, /, *, methods=default_methods, syntax_check=True):
    """
    Example of class builder in action using __slots__ to find fields.

    :param cls: Class to be analysed and modified
    :param methods: MethodMakers to be added to the class
    :param syntax_check: check there are no arguments without defaults
                        after arguments with defaults.
    :return: Modified class
    """
    if not cls:
        return lambda cls_: slotclass(cls_, methods=methods, syntax_check=syntax_check)

    cls = builder(cls, gatherer=slot_gatherer, methods=methods, flags={"slotted": True})

    if syntax_check:
        check_argument_order(cls)

    return cls
