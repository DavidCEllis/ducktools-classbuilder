from ducktools.classbuilder import (
    add_methods,
    get_fields,
    make_unified_gatherer,
    get_generated_code,
    GeneratedCode,
    MethodMaker,
)
from ducktools.classbuilder.prefab import attribute, Attribute, Prefab


class ConverterAttribute(Attribute):
    converter = attribute(default=None)

# This makes the internal field instances into `ConverterAttribute` instead of `Attribute`
# which would be the default for `prefab`
gatherer = make_unified_gatherer(field_type=ConverterAttribute)

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
extra_methods = {setattr_maker}


class ConverterClass(Prefab, gatherer=gatherer):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        add_methods(cls, extra_methods)


if __name__ == "__main__":
    class ConverterEx(ConverterClass):
        unconverted: str
        converted: int = ConverterAttribute(converter=int)

    ex = ConverterEx("42", "42")
    print(ex)
    print()
    code = get_generated_code(ConverterEx)

    for k in sorted(code):
        print(code[k].source_code)
