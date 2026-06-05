# Don't use __future__ annotations with get_ns_annotations in this case
# as it doesn't evaluate string annotations.

import sys
import types
from functools import wraps
from typing import Annotated, Any, ClassVar, get_origin

from ducktools.classbuilder.constants import NOTHING
from ducktools.classbuilder.functions import get_methods
from ducktools.classbuilder.prefab import prefab, Prefab, Attribute, attribute, get_attributes

from ducktools.classbuilder.annotations import get_ns_annotations, is_classvar, resolve_type


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
NO_SERIALIZE = FieldModifier(serialize=False)
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

        # Under Python 3.14 these may be `DeferredAnnotations`
        # Resolve them to ForwardRefs
        anno = resolve_type(anno)
        if is_classvar(anno):
            continue

        if get_origin(anno) is Annotated:
            meta = anno.__metadata__
            for v in meta:
                if isinstance(v, FieldModifier):
                    # Merge the modifier arguments to pass to AnnoField
                    modifiers.update(v.modifiers)

            # Extract the actual annotation from the first argument
            anno = anno.__origin__

        if key in cls_dict:
            val = cls_dict[key]
            if isinstance(val, Attribute):
                # Make a new field - DO NOT MODIFY FIELDS IN PLACE
                fld = Attribute.from_field(val, type=anno, **modifiers)
                cls_modifications[key] = NOTHING
            elif not isinstance(val, types.MemberDescriptorType):
                fld = Attribute(default=val, type=anno, **modifiers)
                cls_modifications[key] = NOTHING
            else:
                fld = Attribute(type=anno, **modifiers)
        else:
            fld = Attribute(type=anno, **modifiers)

        cls_fields[key] = fld

    return cls_fields, cls_modifications


# As a decorator
@wraps(prefab)
def annotatedclass(cls=None, **kwargs):
    return prefab(cls, gatherer=annotated_gatherer, **kwargs)


# As a base class with slots
class AnnotatedClass(Prefab, gatherer=annotated_gatherer):
    pass


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
        c: Annotated[list[str], NO_COMPARE] = attribute(default_factory=list)  # type: ignore
        d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
        e: Annotated[str, KW_ONLY, NO_COMPARE]
        if sys.version_info >= (3, 14):
            # Forward references work in 3.14
            f: Annotated[unknown, NO_COMPARE, NO_SERIALIZE] = 42


    class Y(AnnotatedClass):
        x: str
        y: ClassVar[str] = "This should be ignored"
        z: Annotated[ClassVar[str], "Should be ignored"] = "This should also be ignored"  # type: ignore
        a: Annotated[int, NO_INIT] = "Not In __init__ signature"  # type: ignore
        b: Annotated[str, NO_REPR] = "Not In Repr"
        c: Annotated[list[str], NO_COMPARE] = attribute(default_factory=list)  # type: ignore
        d: Annotated[str, IGNORE_ALL] = "Not Anywhere"
        e: Annotated[str, KW_ONLY, NO_COMPARE]
        if sys.version_info >= (3, 14):
            f: Annotated[unknown, NO_COMPARE, NO_SERIALIZE] = 42

    # Unslotted Demo
    ex = X("Value of x", e="Value of e")  # type: ignore
    print(ex, "\n")

    pp(get_attributes(X))
    print("\n")

    # Slotted Demo
    ex = Y("Value of x", e="Value of e")  # type: ignore
    print(ex, "\n")

    print(f"Slots: {Y.__dict__.get('__slots__')}")

    print("\nSource:")

    # Obtain the methods set on the class X
    methods = get_methods(X)

    # Call the code generators to display the source code
    for _, method in sorted(methods.items()):
        # Both classes generate identical source code
        genX = method.code_generator(X)
        genY = method.code_generator(Y)
        assert genX.source_code == genY.source_code

        print(genX.source_code)
