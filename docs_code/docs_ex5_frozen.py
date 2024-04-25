from ducktools.classbuilder import (
    slotclass,
    SlotFields,
    default_methods,
    frozen_setattr_desc,
    frozen_delattr_desc,
)


new_methods = default_methods | {frozen_setattr_desc, frozen_delattr_desc}


def frozen(cls, /):
    return slotclass(cls, methods=new_methods)


if __name__ == "__main__":
    @frozen
    class FrozenEx:
        __slots__ = SlotFields(
            x=6,
            y=9,
            product=42,
        )


    ex = FrozenEx()
    print(ex)

    try:
        ex.y = 7
    except TypeError as e:
        print(e)

    try:
        ex.z = "new value"
    except TypeError as e:
        print(e)

    try:
        del ex.y
    except TypeError as e:
        print(e)
