from ducktools.classbuilder import (
    slotclass,
    get_fields,
    SlotFields,
    MethodMaker,
    default_methods,
)


def setattr_maker(cls):
    # This is a set once __setattr__ method
    # As opposed to some set never methods.
    # This saves rewriting __init__ in this case.

    globs = {
        "object_setattr": object.__setattr__
    }

    field_names = set(get_fields(cls).keys())

    code = (
        f"def __setattr__(self, name, value):\n"
        f"    fields = {field_names!r}\n"
        f"    if name in fields and not hasattr(self, name):\n"
        f"        object_setattr(self, name, value)\n"
        f"    else:\n"
        f'        raise TypeError(f"{{type(self).__name__!r}} object does not support attribute assignment")'
    )
    return code, globs


def delattr_maker(cls):
    code = (
        f"def __delattr__(self, name):\n"
        f'    raise TypeError(f"{{type(self).__name__!r}} object does not support attribute deletion")'
    )
    globs = {}
    return code, globs


setattr_desc = MethodMaker("__setattr__", setattr_maker)
delattr_desc = MethodMaker("__delattr__", delattr_maker)

new_methods = frozenset(default_methods | {setattr_desc, delattr_desc})


def frozen(cls, /):
    return slotclass(cls, methods=new_methods)


if __name__ == "__main__":
    @frozen
    class FrozenEx:
        __slots__ = SlotFields(
            x=6,
            y=9,
            product=42,
        )


    ex = FrozenEx()
    print(ex)

    try:
        ex.y = 7
    except TypeError as e:
        print(e)

    try:
        ex.z = "new value"
    except TypeError as e:
        print(e)

    try:
        del ex.y
    except TypeError as e:
        print(e)
