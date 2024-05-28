from ducktools.classbuilder import (
    eq_maker,
    get_fields,
    init_maker,
    slotclass,
    Field,
    SlotFields,
    MethodMaker,
)


class FieldExt(Field):
    __slots__ = SlotFields(repr=True)


def repr_exclude_generator(cls):
    fields = get_fields(cls)

    # Use getattr with default True for the condition so
    # regular fields without the 'repr' field still work
    content = ", ".join(
        f"{name}={{self.{name}!r}}"
        for name, field in fields.items()
        if getattr(field, "repr", True)
    )
    code = (
        f"def __repr__(self):\n"
        f"    return f'{{type(self).__qualname__}}({content})'\n"
    )
    globs = {}
    return code, globs


repr_exclude_maker = MethodMaker("__repr__", repr_exclude_generator)


if __name__ == "__main__":

    methods = frozenset({init_maker, eq_maker, repr_exclude_maker})

    @slotclass(methods=methods)
    class Example:
        __slots__ = SlotFields(
            the_answer=42,
            the_question=Field(
                default="What do you get if you multiply six by nine?",
                doc="Life, the Universe, and Everything",
            ),
            the_book=FieldExt(
                default="The Hitchhiker's Guide to the Galaxy",
                repr=False,
            )
        )

    ex = Example()
    print(ex)
    print(ex.the_book)
