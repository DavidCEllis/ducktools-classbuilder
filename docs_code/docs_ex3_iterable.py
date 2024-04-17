from ducktools.classbuilder import (
    default_methods, get_fields, slotclass, MethodMaker, SlotFields
)


def iter_maker(cls):
    field_names = get_fields(cls).keys()
    field_yield = "\n".join(f"    yield self.{f}" for f in field_names)
    code = (
        f"def __iter__(self):\n"
        f"{field_yield}"
    )
    globs = {}
    return code, globs


iter_desc = MethodMaker("__iter__", iter_maker)
new_methods = frozenset(default_methods | {iter_desc})


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
