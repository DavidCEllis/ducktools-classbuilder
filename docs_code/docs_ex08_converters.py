from ducktools.classbuilder import (
    builder,
    default_methods,
    get_fields,
    slot_gatherer,
    Field,
    GeneratedCode,
    SlotFields,
    MethodMaker,
)


class ConverterField(Field):
    converter = Field(default=None)


def setattr_generator(cls, funcname="__setattr__"):
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
        f"def {funcname}(self, name, value):\n"
        f"    if conv := _converters.get(name):\n"
        f"        _object_setattr(self, name, conv(value))\n"
        f"    else:\n"
        f"        _object_setattr(self, name, value)\n"
    )

    return GeneratedCode(code, globs)


setattr_maker = MethodMaker("__setattr__", setattr_generator)
methods = frozenset(default_methods | {setattr_maker})


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
