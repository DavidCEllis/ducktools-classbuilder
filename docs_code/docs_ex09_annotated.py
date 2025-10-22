import types
from typing import Annotated, Any, ClassVar, get_origin

from ducktools.classbuilder import (
    builder,
    default_methods,
    get_fields,
    get_methods,
    pre_gathered_gatherer,
    Field,
    SlotMakerMeta,
    GATHERED_DATA,
    NOTHING,
)

from ducktools.classbuilder.annotations import get_ns_annotations


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
def annotated_gatherer(cls_or_ns):
    if isinstance(cls_or_ns, (types.MappingProxyType, dict)):
        cls_dict = cls_or_ns
    else:
        cls_dict = cls_or_ns.__dict__

    cls_annotations = get_ns_annotations(cls_dict)
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

        if key in cls_dict:
            val = cls_dict[key]
            if isinstance(val, Field):
                # Make a new field - DO NOT MODIFY FIELDS IN PLACE
                fld = Field.from_field(val, type=anno, **modifiers)
                cls_modifications[key] = NOTHING
            elif not isinstance(val, types.MemberDescriptorType):
                fld = Field(default=val, type=anno, **modifiers)
                cls_modifications[key] = NOTHING
            else:
                fld = Field(type=anno, **modifiers)
        else:
            fld = Field(type=anno, **modifiers)

        cls_fields[key] = fld

    return cls_fields, cls_modifications


# As a decorator
def annotatedclass(cls=None, *, kw_only=False):
    if not cls:
        return lambda cls_: annotatedclass(cls_, kw_only=kw_only)

    return builder(
        cls,
        gatherer=annotated_gatherer,
        methods=default_methods,
        flags={"slotted": False, "kw_only": kw_only}
    )


# As a base class with slots
class AnnotatedClass(metaclass=SlotMakerMeta, gatherer=annotated_gatherer):
    
    def __init_subclass__(cls, kw_only=False, **kwargs):
        pre_gathered = GATHERED_DATA in cls.__dict__
        slots = "__slots__" in cls.__dict__

        # if slots is True then fields will already be present in __slots__
        # Use the slot_gatherer for this case
        gatherer = pre_gathered_gatherer if pre_gathered else annotated_gatherer

        builder(
            cls,
            gatherer=gatherer,
            methods=default_methods,
            flags={"slotted": slots, "kw_only": kw_only}
        )

        super().__init_subclass__(**kwargs)


if __name__ == "__main__":
    from pprint import pp

    # Make classes, one via decorator one via subclass
    @annotatedclass
    class X:
        x: str
        y: ClassVar[str] = "This should be ignored"
        z: Annotated[ClassVar[str], "Should be ignored"] = "This should also be ignored"  # type: ignore
        a: Annotated[int, NO_INIT] = "Not In __init__ signature"  # type: ignore
        b: Annotated[str, NO_REPR] = "Not In Repr"
        c: Annotated[list[str], NO_COMPARE] = Field(default_factory=list)  # type: ignore
        d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
        e: Annotated[str, KW_ONLY, NO_COMPARE]


    class Y(AnnotatedClass):
        x: str
        y: ClassVar[str] = "This should be ignored"
        z: Annotated[ClassVar[str], "Should be ignored"] = "This should also be ignored"  # type: ignore
        a: Annotated[int, NO_INIT] = "Not In __init__ signature"  # type: ignore
        b: Annotated[str, NO_REPR] = "Not In Repr"
        c: Annotated[list[str], NO_COMPARE] = Field(default_factory=list)  # type: ignore
        d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
        e: Annotated[str, KW_ONLY, NO_COMPARE]


    # Unslotted Demo
    ex = X("Value of x", e="Value of e")  # type: ignore
    print(ex, "\n")

    pp(get_fields(X))
    print("\n")

    # Slotted Demo
    ex = Y("Value of x", e="Value of e")  # type: ignore
    print(ex, "\n")

    print(f"Slots: {Y.__dict__.get('__slots__')}")

    print("\nSource:")

    # Obtain the methods set on the class X
    methods = get_methods(X)

    # Call the code generators to display the source code
    for method in methods.values():
        # Both classes generate identical source code
        genX = method.code_generator(X)
        genY = method.code_generator(Y)
        assert genX == genY

        print(genX.source_code)
