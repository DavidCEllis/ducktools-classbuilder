from ducktools.classbuilder import (
    SlotMakerMeta,
    builder,
    check_argument_order,
    default_methods,
    unified_gatherer,
)


class AnnotationClass(metaclass=SlotMakerMeta):
    __slots__ = {}

    def __init_subclass__(
            cls,
            methods=default_methods,
            gatherer=unified_gatherer,
            **kwargs
    ):
        # Check class dict otherwise this will always be True as this base
        # class uses slots.
        slots = "__slots__" in cls.__dict__

        builder(cls, gatherer=gatherer, methods=methods, flags={"slotted": slots})
        check_argument_order(cls)
        super().__init_subclass__(**kwargs)


class AnnotatedDC(AnnotationClass):
    the_answer: int = 42
    the_question: str = "What do you get if you multiply six by nine?"


ex = AnnotatedDC()
print(ex)
