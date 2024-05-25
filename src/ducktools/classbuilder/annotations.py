import sys

from . import (
    Field, NOTHING, SlotFields,
    builder, check_argument_order, slot_gatherer, default_methods,
)


def eval_hint(hint, obj_globals=None, obj_locals=None):
    # Can 'eval' mutate these like exec?
    globs = obj_globals.copy() if obj_globals is not None else None
    locs = obj_locals.copy() if obj_locals is not None else None
    while isinstance(hint, str):
        try:
            hint = eval(hint, globs, locs)
        except (NameError, TypeError):  # Subscripting in strings can give TypeError
            break
    return hint


def is_classvar(hint):
    _typing = sys.modules.get("typing")
    if _typing:
        # Annotated is a nightmare I'm never waking up from
        # 3.8 and 3.9 need Annotated from typing_extensions
        # 3.8 also needs get_origin from typing_extensions
        if sys.version_info < (3, 10):
            _typing_extensions = sys.modules.get("typing_extensions")
            if _typing_extensions:
                _Annotated = _typing_extensions.Annotated
                _get_origin = _typing_extensions.get_origin
            else:
                _Annotated, _get_origin = None, None
        else:
            _Annotated = _typing.Annotated
            _get_origin = _typing.get_origin

        if _Annotated and _get_origin(hint) is _Annotated:
            hint = getattr(hint, "__origin__", None)

        if (
            hint is _typing.ClassVar
            or getattr(hint, "__origin__", None) is _typing.ClassVar
        ):
            return True
    return False


class SlotMakerMeta(type):
    """
    Metaclass to convert annotations to slots.

    Will not convert `ClassVar` hinted values.
    """
    def __new__(cls, name, bases, ns, slots=True, **kwargs):

        # Obtain slots from annotations
        if "__slots__" not in ns and slots:
            try:
                obj_modulename = ns["__module__"]
            except KeyError:
                obj_module = None
            else:
                obj_module = sys.modules.get(obj_modulename, None)

            obj_globals = getattr(obj_module, "__dict__", None)

            cls_annotations = ns.get("__annotations__", {})
            cls_slots = SlotFields({
                k: ns.pop(k, NOTHING)
                for k, v in cls_annotations.items()
                if not is_classvar(eval_hint(v, obj_globals=obj_globals, obj_locals=ns))
            })
            ns["__slots__"] = cls_slots

        # Make new slotted class
        new_cls = super().__new__(cls, name, bases, ns, **kwargs)

        return new_cls


def make_annotation_gatherer(
    field_type=Field,
    leave_default_values=True,
):
    """
    Create a new annotation gatherer that will work with `Field` instances
    of the creators definition.

    :param field_type: The `Field` classes to be used when gathering fields
    :param leave_default_values: Set to True if the gatherer should leave
                                 default values in place as class variables.
    :return: An annotation gatherer with these settings.
    """
    def field_annotation_gatherer(cls):
        cls_annotations = cls.__dict__.get("__annotations__", {})

        cls_fields: dict[str, field_type] = {}

        modifications = {}

        cls_locals = dict(vars(cls))
        cls_globals = {}

        module_name = getattr(cls, '__module__', None)
        if module_name:
            module = sys.modules.get(module_name, None)
            if module:
                cls_globals = getattr(module, '__dict__', None)

        for k, v in cls_annotations.items():
            hint = eval_hint(v, cls_globals, cls_locals)
            # Ignore ClassVar
            if is_classvar(hint):
                continue

            attrib = getattr(cls, k, NOTHING)

            if attrib is not NOTHING:
                if isinstance(attrib, field_type):
                    attrib = field_type.from_field(attrib, type=v)

                    if attrib.default is not NOTHING and leave_default_values:
                        modifications[k] = attrib.default
                    else:
                        # NOTHING sentinel indicates a value should be removed
                        modifications[k] = NOTHING
                else:
                    attrib = field_type(default=attrib, type=v)
                    if not leave_default_values:
                        modifications[k] = NOTHING
            else:
                attrib = field_type(type=v)

            cls_fields[k] = attrib

        return cls_fields, modifications

    return field_annotation_gatherer


annotation_gatherer = make_annotation_gatherer()


class AnnotationClass(metaclass=SlotMakerMeta):
    def __init_subclass__(cls, methods=default_methods, **kwargs):
        # Check class dict otherwise this will always be True as this base
        # class uses slots.

        slots = "__slots__" in cls.__dict__

        gatherer = slot_gatherer if slots else annotation_gatherer

        builder(cls, gatherer=gatherer, methods=methods, flags={"slotted": slots})
        check_argument_order(cls)
        super().__init_subclass__(**kwargs)
