import inspect
from typing import Annotated, Any, ClassVar, get_origin

from ducktools.classbuilder import builder, default_methods, Field


def annotated_gatherer(cls: type) -> dict[str, Any]:
    cls_annotations = inspect.get_annotations(cls, eval_str=True)
    cls_fields = {}

    for key, anno in cls_annotations.items():
        # Is there another way to do this?
        if get_origin(anno) is Annotated:
            typ = anno.__args__[0]
            meta = anno.__metadata__
            for v in meta:
                if isinstance(v, Field):
                    fld = Field.from_field(v, type=typ)
                    break
            else:
                fld = Field(type=typ)
        elif anno is ClassVar or get_origin(anno) is ClassVar:
            fld = None
        else:
            typ = anno
            fld = Field(type=typ)

        if fld:
            cls_fields[key] = fld
            if key in cls.__dict__ and "__slots__" not in cls.__dict__:
                raise AttributeError("No attributes! Only Annotations!")

    return cls_fields


def annotationsclass(cls):
    return builder(cls, gatherer=annotated_gatherer, methods=default_methods)


@annotationsclass
class X:
    x: str
    y: ClassVar[str] = "This is okay"
    a: Annotated[int, Field(default=1)]
    b: Annotated[str, Field(default="example")]
    c: Annotated[list[str], Field(default_factory=list)]


print(X("Testing"))
print(X.y)
