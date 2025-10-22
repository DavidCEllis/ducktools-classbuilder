from ducktools.classbuilder import (
    default_methods,
    get_fields,
    slotclass,
    GeneratedCode,
    MethodMaker,
    SlotFields,
)


def iter_generator(cls, funcname="__iter__"):
    field_names = get_fields(cls).keys()
    field_yield = "\n".join(f"    yield self.{f}" for f in field_names)
    if not field_yield:
        field_yield = "    yield from ()"
    code = f"def {funcname}(self):\n{field_yield}"
    globs = {}
    return GeneratedCode(code, globs)


iter_maker = MethodMaker("__iter__", iter_generator)
new_methods = frozenset(default_methods | {iter_maker})


def iterclass(cls=None, /):
    return slotclass(cls, methods=new_methods)


if __name__ == "__main__":
    @iterclass
    class IterDemo:
        __slots__ = SlotFields(
            a=1,
            b=2,
            c=3,
            d=4,
            e=5,
        )

    ex = IterDemo()
    print([item for item in ex])


    @iterclass
    class IterDemo:
        __slots__ = SlotFields()


    ex = IterDemo()
    print([item for item in ex])