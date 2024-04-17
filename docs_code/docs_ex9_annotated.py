import inspect
from pprint import pp
from typing import Annotated, Any, ClassVar, get_origin

from ducktools.classbuilder import (
    builder,
    fieldclass,
    get_fields,
    get_internals,
    Field,
    MethodMaker,
    SlotFields,
    NOTHING,
)


# New equivalent to dataclasses "Field", these still need to be created
# in order to generate the magic methods correctly.
@fieldclass
class AnnoField(Field):
    __slots__ = SlotFields(
        init=True,
        repr=True,
        compare=True,
        kw_only=False,
    )


# Modifying objects
class FieldModifier:
    __slots__ = ("modifiers", )
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


KW_ONLY = FieldModifier(kw_only=True)
NO_INIT = FieldModifier(init=False)
NO_REPR = FieldModifier(repr=False)
NO_COMPARE = FieldModifier(compare=False)
IGNORE_ALL = FieldModifier(init=False, repr=False, compare=False)


def annotated_gatherer(cls: type) -> dict[str, Any]:
    # String annotations *MUST* be evaluated for this to work
    # dataclasses currently does not require this
    cls_annotations = inspect.get_annotations(cls, eval_str=True)
    cls_fields = {}

    for key, anno in cls_annotations.items():
        modifiers = {}
        typ = NOTHING

        if get_origin(anno) is Annotated:
            typ = anno.__args__[0]
            meta = anno.__metadata__
            modifiers = {}
            for v in meta:
                if isinstance(v, FieldModifier):
                    modifiers.update(v.modifiers)

        elif not (anno is ClassVar or get_origin(anno) is ClassVar):
            typ = anno

        if typ is not NOTHING:
            if key in cls.__dict__ and "__slots__" not in cls.__dict__:
                val = cls.__dict__[key]
                if isinstance(val, Field):
                    fld = AnnoField.from_field(val, type=typ, **modifiers)
                else:
                    fld = AnnoField(default=val, type=typ, **modifiers)
            else:
                fld = AnnoField(type=typ, **modifiers)

            cls_fields[key] = fld

    return cls_fields


def init_maker(cls):

    internals = get_internals(cls)
    fields = get_fields(cls)

    arglist = []
    kw_only_arglist = []

    assignments = []
    globs = {}

    # Whole class kw_only
    kw_only = internals.get("kw_only", False)
    if kw_only:
        arglist.append("*")

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


def repr_maker(cls):
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


def eq_maker(cls):
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


init_method = MethodMaker("__init__", init_maker)
repr_method = MethodMaker("__repr__", repr_maker)
eq_method = MethodMaker("__eq__", eq_maker)

methods = {init_method, repr_method, eq_method}


def annotationsclass(cls=None, *, kw_only=False):
    if not cls:
        return lambda cls_: annotationsclass(cls_, kw_only=kw_only)

    cls = builder(cls, gatherer=annotated_gatherer, methods=methods)

    internals = get_internals(cls)
    internals["kw_only"] = kw_only

    return cls


@annotationsclass
class X:
    x: str
    y: ClassVar[str] = "This is okay"
    a: Annotated[int, NO_INIT] = "Not In __init__ signature"
    b: Annotated[str, NO_REPR] = "Not In Repr"
    c: Annotated[list[str], NO_COMPARE] = AnnoField(default_factory=list)
    d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
    e: Annotated[str, KW_ONLY, NO_COMPARE]


ex = X("Value of x", e="Value of e")

print(ex, "\n")

pp(get_fields(X))
print("\nSource:")
print(init_maker(X)[0])
print(eq_maker(X)[0])
print(repr_maker(X)[0])
