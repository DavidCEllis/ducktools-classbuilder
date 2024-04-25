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
import sys

__version__ = "v0.4.0"

# Change this name if you make heavy modifications
INTERNALS_DICT = "__classbuilder_internals__"


# If testing, make Field classes frozen to make sure attributes are not
# overwritten. When running this is a performance penalty so it is not required.
_UNDER_TESTING = "pytest" in sys.modules


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


def _get_inst_fields(inst):
    # This is an internal helper for constructing new
    # 'Field' instances from existing ones.
    return {
        k: getattr(inst, k)
        for k in get_fields(type(inst))
    }


# As 'None' can be a meaningful default we need a sentinel value
# to use to show no value has been provided.
class _NothingType:
    def __repr__(self):
        return "<NOTHING OBJECT>"


NOTHING = _NothingType()


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

    def __get__(self, instance, cls):
        local_vars = {}
        code, globs = self.code_generator(cls)
        exec(code, globs, local_vars)
        method = local_vars.get(self.funcname)
        method.__qualname__ = f"{cls.__qualname__}.{self.funcname}"

        # Replace this descriptor on the class with the generated function
        setattr(cls, self.funcname, method)

        # Use 'get' to return the generated function as a bound method
        # instead of as a regular function for first usage.
        return method.__get__(instance, cls)


def get_init_maker(null=NOTHING, extra_code=None):
    def cls_init_maker(cls):
        fields = get_fields(cls)
        flags = get_flags(cls)

        arglist = []
        assignments = []
        globs = {}

        if flags.get("kw_only", False):
            arglist.append("*")

        for k, v in fields.items():
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

            arglist.append(arg)
            assignments.append(assignment)

        args = ", ".join(arglist)
        assigns = "\n    ".join(assignments) if assignments else "pass\n"
        code = (
            f"def __init__(self, {args}):\n" 
            f"    {assigns}\n"
        )
        # Handle additional function calls
        # Used for validate_field on fieldclasses
        if extra_code:
            for line in extra_code:
                code += f"    {line}\n"

        return code, globs

    return cls_init_maker


init_maker = get_init_maker()


def repr_maker(cls):
    fields = get_fields(cls)
    content = ", ".join(
        f"{name}={{self.{name}!r}}"
        for name, attrib in fields.items()
    )
    code = (
        f"def __repr__(self):\n"
        f"    return f'{{type(self).__qualname__}}({content})'\n"
    )
    globs = {}
    return code, globs


def eq_maker(cls):
    class_comparison = "self.__class__ is other.__class__"
    field_names = get_fields(cls)

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


def frozen_setattr_maker(cls):
    globs = {}
    field_names = set(get_fields(cls))
    flags = get_flags(cls)

    globs["__field_names"] = field_names

    # Better to be safe and use the method that works in both cases
    # if somehow slotted has not been set.
    if flags.get("slotted", True):
        globs["__setattr_func"] = object.__setattr__
        setattr_method = "__setattr_func(self, name, value)"
    else:
        setattr_method = "self.__dict__[name] = value"

    body = (
        f"    if hasattr(self, name) or name not in __field_names:\n"
        f'        raise TypeError(\n'
        f'            f"{{type(self).__name__!r}} object does not support "'
        f'            f"attribute assignment"\n'
        f'        )\n'
        f"    else:\n"
        f"        {setattr_method}\n"
    )
    code = f"def __setattr__(self, name, value):\n{body}"

    return code, globs


def frozen_delattr_maker(cls):
    body = (
        '    raise TypeError(\n'
        '        f"{type(self).__name__!r} object "\n'
        '        f"does not support attribute deletion"\n'
        '    )\n'
    )
    code = f"def __delattr__(self, name):\n{body}"
    globs = {}
    return code, globs


# As only the __get__ method refers to the class we can use the same
# Descriptor instances for every class.
init_desc = MethodMaker("__init__", init_maker)
repr_desc = MethodMaker("__repr__", repr_maker)
eq_desc = MethodMaker("__eq__", eq_maker)
frozen_setattr_desc = MethodMaker("__setattr__", frozen_setattr_maker)
frozen_delattr_desc = MethodMaker("__delattr__", frozen_delattr_maker)
default_methods = frozenset({init_desc, repr_desc, eq_desc})


def builder(cls=None, /, *, gatherer, methods, flags=None):
    """
    The main builder for class generation

    :param cls: Class to be analysed and have methods generated
    :param gatherer: Function to gather field information
    :type gatherer: Callable[[type], dict[str, Field]]
    :param methods: MethodMakers to add to the class
    :type methods: set[MethodMaker]
    :param flags: additional flags to store in the internals dictionary
                  for use by method generators.
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

    cls_fields = gatherer(cls)
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
    for method in methods:
        setattr(cls, method.funcname, method)

    return cls


# The Field class can finally be defined.
# The __init__ method has to be written manually so Fields can be created
# However after this, the other methods can be generated.
class Field:
    """
    A basic class to handle the assignment of defaults/factories with
    some metadata.

    Intended to be extendable by subclasses for additional features.
    """
    __slots__ = {
        "default": "Standard default value to be used for attributes with"
                   "this field.",
        "default_factory": "A 0 argument function to be called to generate "
                           "a default value, useful for mutable objects like "
                           "lists.",
        "type": "The type of the attribute to be assigned by this field.",
        "doc": "The documentation that appears when calling help(...) on the class."
    }

    # noinspection PyShadowingBuiltins
    def __init__(
        self,
        *,
        default=NOTHING,
        default_factory=NOTHING,
        type=NOTHING,
        doc=None,
    ):
        self.default = default
        self.default_factory = default_factory
        self.type = type
        self.doc = doc

        self.validate_field()

    def validate_field(self):
        if self.default is not NOTHING and self.default_factory is not NOTHING:
            raise AttributeError(
                "Cannot define both a default value and a default factory."
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


# Use the builder to generate __repr__ and __eq__ methods
# and pretend `Field` was a built class all along.
_field_internal = {
    "default": Field(default=NOTHING),
    "default_factory": Field(default=NOTHING),
    "type": Field(default=NOTHING),
    "doc": Field(default=None),
}

_field_methods = {repr_desc, eq_desc}
if _UNDER_TESTING:
    _field_methods.update({frozen_setattr_desc, frozen_delattr_desc})

builder(
    Field,
    gatherer=lambda cls_: _field_internal,
    methods=_field_methods,
    flags={"slotted": True, "kw_only": True},
)


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


def make_slot_gatherer(field_type=Field):
    def field_slot_gatherer(cls):
        """
        Gather field information for class generation based on __slots__

        :param cls: Class to gather field information from
        :return: dict of field_name: Field(...)
        """
        cls_slots = cls.__dict__.get("__slots__", None)

        if not isinstance(cls_slots, SlotFields):
            raise TypeError(
                "__slots__ must be an instance of SlotFields "
                "in order to generate a slotclass"
            )

        cls_annotations = cls.__dict__.get("__annotations__", {})
        cls_fields = {}
        slot_replacement = {}

        for k, v in cls_slots.items():
            if isinstance(v, field_type):
                attrib = v
                if attrib.type is not NOTHING:
                    cls_annotations[k] = attrib.type
            else:
                # Plain values treated as defaults
                attrib = field_type(default=v)

            slot_replacement[k] = attrib.doc
            cls_fields[k] = attrib

        # Replace the SlotAttributes instance with a regular dict
        # So that help() works
        setattr(cls, "__slots__", slot_replacement)

        # Update annotations with any types from the slots assignment
        setattr(cls, "__annotations__", cls_annotations)
        return cls_fields

    return field_slot_gatherer


slot_gatherer = make_slot_gatherer()


# Annotation gathering tools
def is_classvar(hint):
    _typing = sys.modules.get("typing")

    if _typing:
        # Annotated is a nightmare I'm never waking up from
        # 3.8 and 3.9 need Annotated from typing_extensions
        # 3.8 also needs get_origin from typing_extensions
        if sys.version_info < (3, 10):
            _typing_extensions = sys.modules.get("typing_extensions")
            if _typing_extensions:
                _Annotated = _typing_extensions.Annotated
                _get_origin = _typing_extensions.get_origin
            else:
                _Annotated, _get_origin = None, None
        else:
            _Annotated = _typing.Annotated
            _get_origin = _typing.get_origin

        if _Annotated and _get_origin(hint) is _Annotated:
            hint = getattr(hint, "__origin__", None)

        if (
            hint is _typing.ClassVar
            or getattr(hint, "__origin__", None) is _typing.ClassVar
        ):
            return True
        # String used as annotation
        elif isinstance(hint, str) and "ClassVar" in hint:
            return True
    return False


def make_annotation_gatherer(field_type=Field, leave_default_values=True):
    """
    Create a new annotation gatherer that will work with `Field` instances
    of the creators definition.

    :param field_type: The `Field` classes to be used when gathering fields
    :param leave_default_values: Set to True if the gatherer should leave
                                 default values in place as class variables.
    :return: An annotation gatherer with these settings.
    """
    def field_annotation_gatherer(cls):
        cls_annotations = cls.__dict__.get("__annotations__", {})

        cls_fields: dict[str, field_type] = {}

        for k, v in cls_annotations.items():
            # Ignore ClassVar
            if is_classvar(v):
                continue

            attrib = getattr(cls, k, NOTHING)

            if attrib is not NOTHING:
                if isinstance(attrib, field_type):
                    attrib = field_type.from_field(attrib, type=v)
                    if attrib.default is not NOTHING and leave_default_values:
                        setattr(cls, k, attrib.default)
                    else:
                        delattr(cls, k)
                else:
                    attrib = field_type(default=attrib, type=v)
                    if not leave_default_values:
                        delattr(cls, k)

            else:
                attrib = field_type(type=v)

            cls_fields[k] = attrib

        return cls_fields

    return field_annotation_gatherer


annotation_gatherer = make_annotation_gatherer()


def check_argument_order(cls):
    """
    Raise a SyntaxError if the argument order will be invalid for a generated
    `__init__` function.

    :param cls: class being built
    """
    fields = get_fields(cls)
    used_default = False
    for k, v in fields.items():
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


def annotationclass(cls=None, /, *, methods=default_methods):
    if not cls:
        return lambda cls_: annotationclass(cls_, methods=methods)

    cls = builder(cls, gatherer=annotation_gatherer, methods=methods, flags={"slotted": False})

    check_argument_order(cls)

    return cls


_field_init_desc = MethodMaker(
    funcname="__init__",
    code_generator=get_init_maker(
        null=_NothingType(),
        extra_code=["self.validate_field()"],
    )
)


def fieldclass(cls=None, /, *, frozen=False):
    """
    This is a special decorator for making Field subclasses using __slots__.
    This works by forcing the __init__ method to treat NOTHING as a regular
    value. This means *all* instance attributes always have defaults.

    :param cls: Field subclass
    :param frozen: Make the field class a frozen class.
                   Not enabled by default for performance reasons.
    :return: Modified subclass
    """
    if not cls:
        return lambda cls_: fieldclass(cls_, frozen=frozen)

    field_methods = {_field_init_desc, repr_desc, eq_desc}

    # Always freeze when running tests
    if frozen or _UNDER_TESTING:
        field_methods.update({frozen_setattr_desc, frozen_delattr_desc})

    cls = builder(
        cls,
        gatherer=slot_gatherer,
        methods=field_methods,
        flags={"slotted": True, "kw_only": True}
    )

    return cls
