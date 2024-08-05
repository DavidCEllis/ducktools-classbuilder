from ducktools.classbuilder import (
    builder,
    default_methods,
    get_fields,
    get_flags,
    frozen_setattr_maker,
    frozen_delattr_maker,
    make_unified_gatherer,
    Field,
    GeneratedCode,
    MethodMaker,
)


class FreezableField(Field):
    frozen: bool = False


def setattr_generator(cls, funcname="__setattr__"):
    globs = {}

    flags = get_flags(cls)
    fields = get_fields(cls)

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

    return GeneratedCode(code, globs)


def delattr_generator(cls, funcname="__delattr__"):
    globs = {}

    flags = get_flags(cls)
    fields = get_fields(cls)

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

    return GeneratedCode(code, globs)


frozen_setattr_field_maker = MethodMaker("__setattr__", setattr_generator)
frozen_delattr_field_maker = MethodMaker("__delattr__", delattr_generator)


gatherer = make_unified_gatherer(FreezableField, leave_default_values=True)


def freezable(cls=None, /, *, frozen=False):
    if cls is None:
        return lambda cls_: freezable(cls_, frozen=frozen)

    # To make a slotted class use a base class with metaclass
    flags = {
        "frozen": frozen,
        "slotted": False,
    }

    cls = builder(
        cls,
        gatherer=gatherer,
        methods=default_methods,
        flags=flags,
    )

    # Frozen attributes need to be added afterwards
    # Due to the need to know if frozen fields exist
    if frozen:
        setattr(cls, "__setattr__", frozen_setattr_maker)
        setattr(cls, "__delattr__", frozen_delattr_maker)
    else:
        fields = get_fields(cls)
        frozen_fields = [
            f for f in fields.values()
            if getattr(f, "frozen", False)
        ]
        if frozen_fields:
            setattr(cls, "__setattr__", frozen_setattr_field_maker)
            setattr(cls, "__delattr__", frozen_delattr_field_maker)

    return cls


@freezable(frozen=True)
class X:
    a: int = 2
    b: int = FreezableField(default=12, frozen=True)


x = X()
x.a = 21
x.b = 43

