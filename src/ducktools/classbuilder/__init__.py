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
__version__ = "v0.1.1"

# Change this name if you make heavy modifications
INTERNALS_DICT = "__classbuilder_internals__"


def get_internals(cls):
    """
    Utility function to get the internals dictionary
    or return None.

    As generated classes will always have 'fields'
    and 'local_fields' attributes this will always
    evaluate as 'truthy' if this is a generated class.

    Usage:
       if internals := get_internals(cls):
           ...

    :param cls: generated class
    :return: internals dictionary of the class or None
    """
    return getattr(cls, INTERNALS_DICT, None)


def get_fields(cls):
    """
    Utility function to gather the fields dictionary
    from the class internals.

    :param cls: generated class
    :return: dictionary of keys and Field attribute info
    """
    return getattr(cls, INTERNALS_DICT)["fields"]


def get_inst_fields(inst):
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
        return f"<MethodMaker for {self.funcname} method>"

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


def init_maker(cls, *, null=NOTHING, kw_only=False):
    fields = get_fields(cls)

    arglist = []
    assignments = []
    globs = {}

    if kw_only:
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
    assigns = "\n    ".join(assignments)
    code = f"def __init__(self, {args}):\n" f"    {assigns}\n"
    return code, globs


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


# As only the __get__ method refers to the class we can use the same
# Descriptor instances for every class.
init_desc = MethodMaker("__init__", init_maker)
repr_desc = MethodMaker("__repr__", repr_maker)
eq_desc = MethodMaker("__eq__", eq_maker)
default_methods = frozenset({init_desc, repr_desc, eq_desc})


def builder(cls=None, /, *, gatherer, methods):
    """
    The main builder for class generation

    :param cls: Class to be analysed and have methods generated
    :param gatherer: Function to gather field information
    :type gatherer: Callable[[type], dict[str, Field]]
    :param methods: MethodMakers to add to the class
    :type methods: set[MethodMaker]
    :return: The modified class (the class itself is modified, but this is expected).
    """
    # Handle `None` to make wrapping with a decorator easier.
    if cls is None:
        return lambda cls_: builder(
            cls_,
            gatherer=gatherer,
            methods=methods,
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
                fields.update(get_internals(c)["local_fields"])
            except AttributeError:
                pass

    internals["fields"] = fields

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
        argument_dict = {**get_inst_fields(fld), **kwargs}

        return cls(**argument_dict)


# Use the builder to generate __repr__ and __eq__ methods
# and pretend `Field` was a built class all along.
_field_internal = {
    "default": Field(default=NOTHING),
    "default_factory": Field(default=NOTHING),
    "type": Field(default=NOTHING),
    "doc": Field(default=None),
}

builder(
    Field,
    gatherer=lambda cls_: _field_internal,
    methods=frozenset({repr_desc, eq_desc})
)


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


def slot_gatherer(cls):
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
        if isinstance(v, Field):
            attrib = v
            if v.type is not NOTHING:
                cls_annotations[k] = attrib.type
        else:
            # Plain values treated as defaults
            attrib = Field(default=v)

        slot_replacement[k] = attrib.doc
        cls_fields[k] = attrib

    # Replace the SlotAttributes instance with a regular dict
    # So that help() works
    setattr(cls, "__slots__", slot_replacement)

    # Update annotations with any types from the slots assignment
    setattr(cls, "__annotations__", cls_annotations)
    return cls_fields


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

    cls = builder(cls, gatherer=slot_gatherer, methods=methods)

    if syntax_check:
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

    return cls


def fieldclass(cls):
    """
    This is a special decorator for making Field subclasses using __slots__.
    This works by forcing the __init__ method to treat NOTHING as a regular
    value. This means *all* instance attributes always have defaults.

    :param cls: Field subclass
    :return: Modified subclass
    """

    # Fields need a way to call their validate method
    # So append it to the code from __init__.
    def field_init_func(cls_):
        code, globs = init_maker(cls_, null=field_nothing, kw_only=True)
        code += "    self.validate_field()\n"
        return code, globs

    field_nothing = _NothingType()
    field_init_desc = MethodMaker(
        "__init__",
        field_init_func,
    )
    field_methods = frozenset({field_init_desc, repr_desc, eq_desc})

    cls = builder(
        cls,
        gatherer=slot_gatherer,
        methods=field_methods
    )

    return cls
