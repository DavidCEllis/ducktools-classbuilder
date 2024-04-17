from ducktools.classbuilder import (
    builder,
    default_methods,
    fieldclass,
    get_fields,
    slot_gatherer,
    Field,
    SlotFields,
    MethodMaker,
)


@fieldclass
class ConverterField(Field):
    __slots__ = SlotFields(converter=None)


def setattr_maker(cls):
    fields = get_fields(cls)
    converters = {}
    for k, v in fields.items():
        if conv := getattr(v, "converter", None):
            converters[k] = conv

    globs = {
        "_converters": converters,
        "_object_setattr": object.__setattr__,
    }

    code = (
        f"def __setattr__(self, name, value):\n"
        f"    if conv := _converters.get(name):\n"
        f"        _object_setattr(self, name, conv(value))\n"
        f"    else:\n"
        f"        _object_setattr(self, name, value)\n"
    )

    return code, globs


setattr_desc = MethodMaker("__setattr__", setattr_maker)
methods = frozenset(default_methods | {setattr_desc})


def converterclass(cls, /):
    return builder(cls, gatherer=slot_gatherer, methods=methods)


if __name__ == "__main__":
    @converterclass
    class ConverterEx:
        __slots__ = SlotFields(
            unconverted=ConverterField(),
            converted=ConverterField(converter=int),
        )

    ex = ConverterEx("42", "42")
    print(ex)
