from pprint import pp
from typing import Annotated, Any, ClassVar, get_origin

from ducktools.classbuilder import (
    builder,
    get_fields,
    get_flags,
    Field,
    MethodMaker,
    SlotFields,
    NOTHING,
)

from ducktools.classbuilder.annotations import get_annotations


# First we need a new field that can store these modifications
class AnnoField(Field):
    __slots__ = SlotFields(
        init=True,
        repr=True,
        compare=True,
        kw_only=False,
    )


# Our 'Annotated' tools need to be combinable and need to contain the keyword argument
# and value they are intended to change.
# To this end we make a FieldModifier class that stores the keyword values given in a
# dictionary as 'modifiers'. This makes it easy to merge modifiers later.
class FieldModifier:
    __slots__ = ("modifiers",)
    modifiers: dict[str, Any]

    def __init__(self, **modifiers):
        self.modifiers = modifiers

    def __repr__(self):
        mod_args = ", ".join(f"{k}={v!r}" for k, v in self.modifiers.items())
        return (
            f"{type(self).__name__}({mod_args})"
        )

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return self.modifiers == other.modifiers
        return NotImplemented


# Here we make the modifiers and give them the arguments to Field we
# wish to change with their usage.
KW_ONLY = FieldModifier(kw_only=True)
NO_INIT = FieldModifier(init=False)
NO_REPR = FieldModifier(repr=False)
NO_COMPARE = FieldModifier(compare=False)
IGNORE_ALL = FieldModifier(init=False, repr=False, compare=False)


# Analyse the class and create these new Fields based on the annotations
def annotated_gatherer(cls: type) -> tuple[dict[str, AnnoField], dict[str, Any]]:
    # String annotations *MUST* be able to evaluate for this to work
    # Trying to parse the Annotations as strings would add a *lot* of extra work
    cls_annotations = get_annotations(cls.__dict__)
    cls_fields = {}

    # This gatherer doesn't make any class modifications but still needs
    # To have a dict as a return value
    cls_modifications = {}

    for key, anno in cls_annotations.items():
        modifiers = {}

        if get_origin(anno) is Annotated:
            meta = anno.__metadata__
            for v in meta:
                if isinstance(v, FieldModifier):
                    # Merge the modifier arguments to pass to AnnoField
                    modifiers.update(v.modifiers)

            # Extract the actual annotation from the first argument
            anno = anno.__origin__

        if anno is ClassVar or get_origin(anno) is ClassVar:
            continue

        if key in cls.__dict__ and "__slots__" not in cls.__dict__:
            val = cls.__dict__[key]
            if isinstance(val, Field):
                # Make a new field - DO NOT MODIFY FIELDS IN PLACE
                fld = AnnoField.from_field(val, type=anno, **modifiers)
            else:
                fld = AnnoField(default=val, type=anno, **modifiers)
        else:
            fld = AnnoField(type=anno, **modifiers)

        cls_fields[key] = fld

    return cls_fields, cls_modifications


def init_generator(cls):
    fields = get_fields(cls)
    flags = get_flags(cls)

    arglist = []
    kw_only_arglist = []

    assignments = []
    globs = {}

    # Whole class kw_only
    kw_only = flags.get("kw_only", False)

    for k, v in fields.items():
        if getattr(v, "init", True):
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

            if getattr(v, "kw_only", False) or kw_only:
                kw_only_arglist.append(arg)
            else:
                arglist.append(arg)

            assignments.append(assignment)
        else:
            if v.default is not NOTHING:
                globs[f"_{k}_default"] = v.default
                assignment = f"self.{k} = _{k}_default"
                assignments.append(assignment)
            elif v.default_factory is not NOTHING:
                globs[f"_{k}_factory"] = v.default_factory
                assignment = f"self.{k} = _{k}_factory()"
                assignments.append(assignment)

    if kw_only_arglist:
        arglist.append("*")
        arglist.extend(kw_only_arglist)

    args = ", ".join(arglist)
    assigns = "\n    ".join(assignments)
    code = f"def __init__(self, {args}):\n" f"    {assigns}\n"

    return code, globs


def repr_generator(cls):
    fields = get_fields(cls)
    content = ", ".join(
        f"{name}={{self.{name}!r}}"
        for name, fld in fields.items()
        if getattr(fld, "repr", True)
    )
    code = (
        f"def __repr__(self):\n"
        f"    return f'{{type(self).__qualname__}}({content})'\n"
    )
    globs = {}
    return code, globs


def eq_generator(cls):
    class_comparison = "self.__class__ is other.__class__"
    field_names = [
        name
        for name, fld in get_fields(cls).items()
        if getattr(fld, "compare", True)
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


init_maker = MethodMaker("__init__", init_generator)
repr_maker = MethodMaker("__repr__", repr_generator)
eq_maker = MethodMaker("__eq__", eq_generator)

methods = {init_maker, repr_maker, eq_maker}


def annotationsclass(cls=None, *, kw_only=False):
    if not cls:
        return lambda cls_: annotationsclass(cls_, kw_only=kw_only)

    return builder(
        cls,
        gatherer=annotated_gatherer,
        methods=methods,
        flags={"slotted": False, "kw_only": kw_only}
    )


@annotationsclass
class X:
    x: str
    y: ClassVar[str] = "This should be ignored"
    z: Annotated[ClassVar[str], "Should be ignored"] = "This should also be ignored"
    a: Annotated[int, NO_INIT] = "Not In __init__ signature"
    b: Annotated[str, NO_REPR] = "Not In Repr"
    c: Annotated[list[str], NO_COMPARE] = AnnoField(default_factory=list)
    d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
    e: Annotated[str, KW_ONLY, NO_COMPARE]


ex = X("Value of x", e="Value of e")

print(ex, "\n")

pp(get_fields(X))
print("\nSource:")
print(init_generator(X)[0])
print(eq_generator(X)[0])
print(repr_generator(X)[0])
