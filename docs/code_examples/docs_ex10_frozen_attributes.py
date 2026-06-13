import ducktools.classbuilder as dtbuild
import ducktools.classbuilder.functions as dtfuncs
import ducktools.classbuilder.methods as dtmethods

class FreezableField(dtbuild.Field):
    frozen: bool = False


def setattr_generator(cls, funcname="__setattr__"):
    globs = {}

    flags = dtfuncs.get_flags(cls)
    fields = dtfuncs.get_fields(cls)

    frozen_fields = set(
        name for name, field in fields.items()
        if getattr(field, "frozen", False)
    )

    globs["__frozen_fields"] = frozen_fields

    if flags.get("slotted", True):
        globs["__setattr_func"] = object.__setattr__
        setattr_method = "__setattr_func(self, name, value)"
        attrib_check = "hasattr(self, name)"
    else:
        setattr_method = "self.__dict__[name] = value"
        attrib_check = "name in self.__dict__"

    code = (
        f"def {funcname}(self, name, value):\n"
        f"    if name in __frozen_fields and {attrib_check}:\n"
        f"        raise AttributeError(\n"
        f"            f'Attribute {{name!r}} does not support assignment'\n"
        f"        )\n"
        f"    else:\n"
        f"        {setattr_method}\n"
    )

    return dtmethods.GeneratedCode(code, globs)


def delattr_generator(cls, funcname="__delattr__"):
    globs = {}

    flags = dtfuncs.get_flags(cls)
    fields = dtfuncs.get_fields(cls)

    frozen_fields = set(
        name for name, field in fields.items()
        if getattr(field, "frozen", False)
    )

    globs["__frozen_fields"] = frozen_fields

    if flags.get("slotted", True):
        globs["__delattr_func"] = object.__delattr__
        delattr_method = "__delattr_func(self, name)"
    else:
        delattr_method = "del self.__dict__[name]"

    code = (
        f"def {funcname}(self, name):\n"
        f"    if name in __frozen_fields:"
        f"        raise AttributeError(\n"
        f"            f'Attribute {{name!r}} is frozen and can not be deleted'\n"
        f"        )\n"
        f"    else:\n"
        f"        {delattr_method}\n"
    )

    return dtmethods.GeneratedCode(code, globs)


frozen_setattr_field_maker = dtmethods.MethodMaker("__setattr__", setattr_generator)
frozen_delattr_field_maker = dtmethods.MethodMaker("__delattr__", delattr_generator)
gatherer = dtbuild.make_unified_gatherer(FreezableField)


def freezable(cls=None, /, *, frozen=False):
    if cls is None:
        return lambda cls_: freezable(cls_, frozen=frozen)

    # To make a slotted class use a base class with metaclass
    flags = {"frozen": frozen, "slotted": False}

    cls = dtbuild.builder(
        cls,
        gatherer=gatherer,
        methods=dtbuild.default_methods,
        flags=flags,
    )

    # Frozen attributes need to be added afterwards
    # Due to the need to know if frozen fields exist
    if frozen:
        dtmethods.add_methods(
            cls,
            [dtmethods.frozen_setattr_maker, dtmethods.frozen_delattr_maker]
        )
    else:
        fields = dtfuncs.get_fields(cls)
        has_frozen_fields = False
        for f in fields.values():
            if getattr(f, "frozen", False):
                has_frozen_fields = True
                break

        if has_frozen_fields:
            dtmethods.add_methods(
                cls,
                [frozen_setattr_field_maker, frozen_delattr_field_maker]
            )

    return cls


@freezable
class X:
    a: int = 2
    b: int = FreezableField(default=12, frozen=True)


x = X()
x.a = 21

try:
    x.b = 43
except AttributeError as e:
    print(repr(e))
