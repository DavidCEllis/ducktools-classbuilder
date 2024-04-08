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
__version__ = "v0.1.0"

# Change this name if you make heavy modifications
INTERNALS_DICT = "__classbuilder_internals__"


def get_fields(cls):
    """Utility function to gather the fields from the class internals"""
    return getattr(cls, INTERNALS_DICT)["fields"]


# As 'None' can be a meaningful default we need a sentinel value
# to use to show no value has been provided.
class _NothingType:
    def __repr__(self):
        return "<NOTHING OBJECT>"


NOTHING = _NothingType()


class Field:
    """
    A basic class to handle the assignment of defaults/factories with
    some metadata.

    Intended to be extendable by subclasses for additional features.

    __repr__ and __eq__ methods will extend to include any additional
    __slots__ values defined in subclasses.
    """
    __slots__ = ("default", "default_factory", "type", "doc")

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

    @property
    def _inherited_slots(self):
        attribs = []
        for cls in reversed(self.__class__.__mro__):
            attribs.extend(getattr(cls, "__slots__", ()))
        return attribs

    def __repr__(self):
        flds = ", ".join(
            f"{attrib}={getattr(self, attrib)!r}"
            for attrib in self._inherited_slots
        )
        return (
            f"{self.__class__.__name__}({flds})"
        )

    def __eq__(self, other):
        if type(self) is type(other):
            return all(
                getattr(self, attrib) == getattr(other, attrib)
                for attrib in self._inherited_slots
            )
        return NotImplemented


class MethodMaker:
    """
    The descriptor class to place where methods should be generated.
    This delays the actual generation and `exec` until the method is needed.

    This is used to convert a code generator that returns code and a globals
    dictionary into a descriptor to assign on a generated class.
    """
    def __init__(self, funcname, code_generator):
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


def init_maker(cls):
    fields = get_fields(cls)

    arglist = []
    assignments = []
    globs = {}

    for k, v in fields.items():
        if v.default is not NOTHING:
            globs[f"_{k}_default"] = v.default
            arg = f"{k}=_{k}_default"
            assignment = f"self.{k} = {k}"
        elif v.default_factory is not NOTHING:
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
    attributes = get_fields(cls)
    content = ", ".join(
        f"{name}={{self.{name}!r}}"
        for name, attrib in attributes.items()
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


# Subclass of dict to be identifiable by isinstance checks
# For anything more complicated this could be made into a Mapping
class SlotFields(dict):
    pass


def slot_gatherer(cls):
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


def builder(cls, /, *, gatherer, methods, default_check=True):
    """
    The main builder for class generation

    :param cls: Class to be analysed and have methods generated
    :param gatherer: Function to gather field information
    :param methods: MethodMakers to add to the class
    :param default_check: Check if fields without default values have been
                          defined *after* fields with defaults.
    :return: The modified class (the class is returned so this could be used
             directly as a decorator if desired).
    """
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
                fields.update(getattr(c, INTERNALS_DICT)["local_fields"])
            except AttributeError:
                pass

    if default_check:
        used_default = False
        for k, v in fields.items():
            if v.default is NOTHING and v.default_factory is NOTHING:
                if used_default:
                    raise SyntaxError(
                        f"non-default argument {k!r} follows default argument"
                    )
            else:
                used_default = True

    internals["fields"] = fields

    # Assign all of the method generators
    for method in methods:
        setattr(cls, method.funcname, method)

    return cls


def slotclass(cls=None, /, *, methods=default_methods):
    """
    Example of class builder in action using __slots__ to find fields.

    :param cls: Class to be analysed and modified
    :param methods: MethodMakers to be added to the class
    :return: Modified class
    """
    if cls is None:
        return lambda cls_: builder(cls_, gatherer=slot_gatherer, methods=methods)
    return builder(cls, gatherer=slot_gatherer, methods=methods)
