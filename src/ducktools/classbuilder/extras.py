import sys
import inspect

from . import NOTHING, Field, builder, default_methods, get_fields


# Python 3.10 was the first version that introduced get_annotations
# It makes handling string annotations much simpler, especially for
# ClassVar.
if not hasattr(inspect, "get_annotations"):  # pragma: nocover
    raise ImportError(
        "Import failed: classbuilder extras are only supported on Python 3.10 or later."
    )


def _is_classvar(hint):
    # Avoid importing typing if it's not already used
    # this annotation gatherer uses eval_str=True so it won't deal with
    # string type hints.
    _typing = sys.modules.get("typing")
    if _typing:
        # Handle Annotated[ClassVar[...], ...]
        if _typing.get_origin(hint) is _typing.Annotated:
            hint = getattr(hint, "__origin__")

        if (
            hint is _typing.ClassVar
            or getattr(hint, "__origin__", None) is _typing.ClassVar
        ):
            return True
    return False


def make_annotation_gatherer(field_type=Field, leave_default_values=True):
    """
    Create a new annotation gatherer that will work with `Field` instances
    of the creators definition.

    :param field_type: The `Field` classes to be used when gathering fields
    :param leave_default_values: Set to True if the gatherer should leave
                                 default values in place as class variables.
    :return: An annotation gatherer with these settings.
    """
    def field_annotation_gatherer(cls):
        cls_annotations = inspect.get_annotations(cls, eval_str=True)

        cls_fields: dict[str, field_type] = {}

        for k, v in cls_annotations.items():
            # Ignore ClassVar
            if _is_classvar(v):
                continue

            attrib = getattr(cls, k, NOTHING)

            if attrib is not NOTHING:
                if isinstance(attrib, field_type):
                    attrib = field_type.from_field(attrib, type=v)
                    if attrib.default is not NOTHING and leave_default_values:
                        setattr(cls, k, attrib.default)
                    else:
                        delattr(cls, k)
                else:
                    attrib = field_type(default=attrib, type=v)
                    if not leave_default_values:
                        delattr(cls, k)

            else:
                attrib = field_type(type=v)

            cls_fields[k] = attrib

        return cls_fields

    return field_annotation_gatherer


annotation_gatherer = make_annotation_gatherer()


def annotationclass(cls=None, /, *, methods=default_methods):
    if not cls:
        return lambda cls_: annotationclass(cls_, methods=methods)

    cls = builder(cls, gatherer=annotation_gatherer, methods=methods, flags={"slotted": False})

    fields = get_fields(cls)
    used_default = False
    for k, v in fields.items():
        if v.default is NOTHING and v.default_factory is NOTHING:
            if used_default:
                raise SyntaxError(
                    f"non-default argument {k!r} follows default argument"
                )
        else:
            used_default = True

    return cls
