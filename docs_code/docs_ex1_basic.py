from ducktools.classbuilder import slotclass, Field, SlotFields


@slotclass
class SlottedDC:
    __slots__ = SlotFields(
        the_answer=42,
        the_question=Field(
            default="What do you get if you multiply six by nine?",
            doc="Life, the Universe, and Everything",
        ),
    )


ex = SlottedDC()
print(ex)
help(SlottedDC)
