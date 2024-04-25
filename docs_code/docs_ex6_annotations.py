import sys

from ducktools.classbuilder import builder, default_methods, Field, NOTHING


# Note: for simplicity this doesn't handle `Annotated[ClassVar[...` (except as a string)
#       It's complicated to do so, see the `prefab` _is_classvar code if you need this
def _is_classvar(hint):
    _typing = sys.modules.get("typing")
    if _typing:
        if (
            hint is _typing.ClassVar
            or getattr(hint, "__origin__", None) is _typing.ClassVar
        ):
            return True
        # Attempt to just look for "ClassVar" in the string.
        # Dataclasses does something much more complicated to catch renaming
        elif isinstance(hint, str) and "ClassVar" in hint:
            return True

    return False


def annotation_gatherer(cls):
    cls_annotations = cls.__dict__.get("__annotations__", {})
    cls_fields = {}

    for k, v in cls_annotations.items():
        # Ignore ClassVar
        if _is_classvar(v):
            continue

        attrib = getattr(cls, k, NOTHING)

        if attrib is not NOTHING:
            if isinstance(attrib, Field):
                attrib = Field.from_field(attrib, type=v)
                # Set class attribute values to the default
                # remove 'Field' instances as class attributes otherwise
                if attrib.default is not NOTHING:
                    setattr(cls, k, attrib.default)
                else:
                    delattr(cls, k)
            else:
                attrib = Field(default=attrib, type=v)

        else:
            attrib = Field(type=v)

        cls_fields[k] = attrib

    return cls_fields


def annotation_class(cls=None, /, *, methods=default_methods):
    return builder(cls, gatherer=annotation_gatherer, methods=methods)


if __name__ == "__main__":
    import typing

    @annotation_class
    class H2G2:
        the_answer: int = 42
        the_question: str = Field(
            default="What do you get if you multiply six by nine?",
        )
        the_book: typing.ClassVar[str] = "The Hitchhiker's Guide to the Galaxy"
        the_author: "typing.ClassVar[str]" = "Douglas Adams"

    ex = H2G2()
    print(ex)
    ex2 = H2G2(
        the_question="What is the ultimate answer to the meaning of life, the universe, and everything?"
    )
    print(ex2)

    print(H2G2.the_book)
    print(H2G2.the_author)
