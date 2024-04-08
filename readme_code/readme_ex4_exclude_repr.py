from ducktools.classbuilder import (
    slotclass,
    get_fields,
    init_desc,
    eq_desc,
    Field,
    SlotFields,
    NOTHING,
    MethodMaker,
)


class FieldExt(Field):
    __slots__ = ("repr", )

    def __init__(
            self,
            *,
            default=NOTHING,
            default_factory=NOTHING,
            type=NOTHING,
            doc=None,
            repr=True,
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            type=type,
            doc=doc,
        )
        self.repr = repr


def repr_exclude_maker(cls):
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


repr_desc = MethodMaker("__repr__", repr_exclude_maker)


if __name__ == "__main__":

    methods = frozenset({init_desc, eq_desc, repr_desc})

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
