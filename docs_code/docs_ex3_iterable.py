from ducktools.classbuilder import (
    default_methods,
    get_fields,
    slotclass,
    MethodMaker,
    SlotFields,
)


def iter_generator(cls):
    field_names = get_fields(cls).keys()
    if field_names:
        field_yield = "\n".join(f"    yield self.{f}" for f in field_names)
    else:
        field_yield = "    yield from ()"

    code = (
        f"def __iter__(self):\n"
        f"{field_yield}\n"
    )
    globs = {}
    return code, globs


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
