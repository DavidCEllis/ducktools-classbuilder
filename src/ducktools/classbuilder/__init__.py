# MIT License
#
# Copyright (c) 2024-2026 David C Ellis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# In this module there are some internal bits of circular logic.
#
# 'Field' needs to exist in order to be used in gatherers, but is itself a
# partially constructed class. These constructed attributes are placed on
# 'Field' post construction.
#
# The 'SlotMakerMeta' metaclass generates 'Field' instances to go in __slots__
# but is also the metaclass used to construct 'Field'.
# Field itself sidesteps this by defining __slots__ to avoid that branch.

__lazy_modules__ = [
    "ducktools.classbuilder.annotations",
    "ducktools.classbuilder._version",
]

import os
import sys

try:
    # Use the internal C module if it is available
    from _types import (  # type: ignore
        MemberDescriptorType as _MemberDescriptorType,
        MappingProxyType as _MappingProxyType,
    )
except ImportError:  # pragma: nocover
    from types import (
        MemberDescriptorType as _MemberDescriptorType,
        MappingProxyType as _MappingProxyType,
    )

from .annotations import (
    get_ns_annotations,
    is_classvar,
    resolve_type,
)
from ._version import __version__, __version_tuple__  # noqa: F401
from .constants import (
    _NothingType,
    INTERNALS_DICT,
    META_GATHERER_NAME,
    GATHERED_DATA,
    NOTHING,
    FIELD_NOTHING,
    KW_ONLY,
)
from .functions import (
    build_completed,
    get_fields,
    get_flags,
    get_methods as get_methods,
    get_generated_code as get_generated_code,
    print_generated_code as print_generated_code,
)
from .methods import (
    add_methods,

    init_maker,
    repr_maker,
    eq_maker,
    frozen_setattr_maker,
    frozen_delattr_maker,
    signature_maker,

    GeneratedCode as GeneratedCode,
    MethodMaker as MethodMaker,
    get_init_generator,
    generic_replace_generator,
)


# If testing, make Field classes frozen to make sure attributes are not
# overwritten. When running this is a performance penalty so it is not required.
_UNDER_TESTING = os.environ.get("PYTEST_VERSION") is not None


default_methods = frozenset({init_maker, repr_maker, eq_maker})

# Special `__init__` maker for 'Field' subclasses - needs its own NOTHING option
_field_init_maker = MethodMaker(
    funcname="__init__",
    code_generator=get_init_generator(
        null=FIELD_NOTHING,
        extra_code=["self.validate_field()"],
    ),
)

# Special `__replace__` method for `Field` that will use the internal `_type`
# value instead of the resolved `type` property
def _field_replace_generator(cls, funcname="__replace__"):
    # A special replace generator for FIELD that replaces
    # type with _type
    field_pairs = [
        (k, k if k != "type" else f"_{k}")
        for k, v in get_fields(cls).items()
        if v.init
    ]  # fmt: skip
    return generic_replace_generator(field_pairs, funcname=funcname)

_field_replace_maker = MethodMaker("__replace__", _field_replace_generator)


def builder(
    cls=None,
    /,
    *,
    gatherer,
    methods,
    flags=None,
    fix_signature=True,
    field_getter=get_fields,
):
    """
    The main builder for class generation

    If the GATHERED_DATA attribute exists on the class it will be used instead of
    the provided gatherer.

    :param cls: Class to be analysed and have methods generated
    :param gatherer: Function to gather field information
    :type gatherer: Callable[[type], tuple[dict[str, Field], dict[str, Any]]]
    :param methods: MethodMakers to add to the class
    :type methods: set[MethodMaker]
    :param flags: additional flags to store in the internals dictionary
                  for use by method generators.
    :type flags: None | dict[str, bool]
    :param fix_signature: Add a __signature__ attribute to work-around an issue with
                          inspect.signature incorrectly handling __init__ descriptors.
    :type fix_signature: bool
    :param field_getter: function to use to retrieve fields from parent classes
    :type field_getter: Callable[[type], dict[str, Field]]
    :return: The modified class (the class itself is modified, but this is expected).
    """
    # Handle `None` to make wrapping with a decorator easier.
    if cls is None:
        return lambda cls_: builder(
            cls_,
            gatherer=gatherer,
            methods=methods,
            flags=flags,
            fix_signature=fix_signature,
            field_getter=field_getter,
        )

    # Get from the class dict to avoid getting an inherited internals dict
    internals = cls.__dict__.get(INTERNALS_DICT, {})
    setattr(cls, INTERNALS_DICT, internals)

    # Update or add flags to internals dict
    flag_dict = internals.get("flags", {})
    if flags is not None:
        flag_dict |= flags
    internals["flags"] = flag_dict

    kw_only = flag_dict.get("kw_only", False)
    cls_gathered = cls.__dict__.get(GATHERED_DATA)

    if cls_gathered:
        cls_fields, modifications = cls_gathered
    else:
        cls_fields, modifications = gatherer(cls)

    if kw_only:
        # Update the class fields to make all Fields kw_only
        cls_fields = {
            k: v if v.kw_only else v.__replace__(kw_only=True)
            for k, v in cls_fields.items()
        }

    for name, value in modifications.items():
        if value is NOTHING:
            delattr(cls, name)
        else:
            setattr(cls, name, value)

    internals["local_fields"] = cls_fields

    mro = cls.__mro__[:-1]  # skip 'object' base class
    if mro == (cls,):  # special case of no inheritance.
        fields = cls_fields.copy()
    else:
        fields = {}
        for c in reversed(mro):
            try:
                fields |= field_getter(c, local=True)
            except TypeError:
                pass

    internals["fields"] = fields

    # Assign all of the method generators
    internal_methods = add_methods(cls, methods, internals=internals)

    if "__eq__" in internal_methods and "__hash__" not in internal_methods:
        # If an eq method has been defined and a hash method has not
        # Then the class is not frozen unless the user has
        # defined a hash method
        if "__hash__" not in cls.__dict__:
            setattr(cls, "__hash__", None)

    # Fix for inspect.signature(cls)
    if fix_signature:
        setattr(cls, "__signature__", signature_maker)

    # Add attribute indicating build completed
    internals["build_complete"] = True

    return cls


# Slot gathering tools
# Subclass of dict to be identifiable by isinstance checks
# For anything more complicated this could be made into a Mapping
class SlotFields(dict):
    """
    A plain dict subclass.

    For declaring slotfields there are no additional features required
    other than recognising that this is intended to be used as a class
    generating dict and isn't a regular dictionary that ended up in
    `__slots__`.

    This should be replaced on `__slots__` after fields have been gathered.
    """

    def __repr__(self):
        return f"SlotFields({super().__repr__()})"


class _SlottedCachedProperty:
    # This is a class that is used to wrap both a slot and a cached property
    # externally, users should just use `functools.cached_property` but
    # `SlotMakerMeta` will remove those, add the names to `__slots__`
    # and after constructing the class, replace those slots with these
    # special slotted cached property attributes

    # Unlike regular cached_property this is always attached to a class
    # after it has been constructed, so `attrname` is set in `__init__`
    # and not in `__set_name__`.

    def __init__(self, slot, func, attrname):
        self.slot = slot

        self.func = func
        self.attrname = attrname
        self.__doc__ = self.func.__doc__
        self.__module__ = self.func.__module__

        # Cached methods for faster access
        self._slotget = slot.__get__
        self._slotset = slot.__set__
        self._slotdelete = slot.__delete__

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return self._slotget(instance, owner)
        except AttributeError:
            pass

        result = self.func(instance)

        self._slotset(instance, result)

        return result

    def __repr__(self):
        return f"<slotted cached_property wrapper for {self.attrname!r}>"

    def __set__(self, obj, value):
        self._slotset(obj, value)

    def __delete__(self, obj):
        self._slotdelete(obj)


# Tool to convert annotations to slots as a metaclass
class SlotMakerMeta(type):
    """
    Metaclass to convert annotations or Field(...) attributes to slots.

    Will not convert `ClassVar` hinted values.
    """

    def __new__(
        cls,
        name,
        bases,
        ns,
        slots=True,
        gatherer=None,
        ignore_annotations=None,
        **kwargs,
    ):
        # Slot makers should inherit flags
        for base in bases:
            try:
                flags = get_flags(base).copy()
            except TypeError:
                pass
            else:
                break
        else:
            flags = {"ignore_annotations": False}

        # Set up flags as these may be needed early
        if ignore_annotations is not None:
            flags["ignore_annotations"] = ignore_annotations

        # Assign flags to internals
        ns[INTERNALS_DICT] = {"flags": flags}

        # This should only run if slots=True is declared
        # and __slots__ have not already been defined
        if slots and "__slots__" not in ns:
            # Get existing attributes
            base_attribs = {}
            for base in reversed(bases):
                base_attribs |= base.__dict__

            # Check if a different gatherer has been set in any base classes
            # Default to unified gatherer
            if gatherer is None:
                gatherer = ns.get(META_GATHERER_NAME, None)
                if not gatherer:
                    for base in bases:
                        if g := getattr(base, META_GATHERER_NAME, None):
                            gatherer = g
                            break

                if not gatherer:
                    gatherer = unified_gatherer

            # Set the gatherer in the namespace
            ns[META_GATHERER_NAME] = gatherer

            # Obtain slots from annotations or attributes
            cls_fields, cls_modifications = gatherer(ns)
            for k, v in cls_modifications.items():
                if v is NOTHING:
                    ns.pop(k)
                else:
                    ns[k] = v

            slot_values = {}
            fields = {}
            existing_slot_types = {_MemberDescriptorType, _SlottedCachedProperty}
            for k, v in cls_fields.items():
                # Don't repeat the slots for already slotted values
                inherited_attrib = base_attribs.get(k, NOTHING)
                if (
                    inherited_attrib is NOTHING
                    or type(inherited_attrib) not in existing_slot_types
                ):
                    slot_values[k] = v.doc
                if k not in {"__weakref__", "__dict__"}:
                    fields[k] = v

            # Special case cached_property if there is no `__dict__` attribute
            # In the case where there is a __dict__ it is not necessary to replace
            # the cached_property attribute as the dict can be used, otherwise
            # it needs to be replaced in order to store the value in the slot
            # created.
            # Dict access is faster if there is a __dict__ available.
            cached_properties = {}

            if "__dict__" not in slot_values and "__dict__" not in base_attribs:
                # Don't import functools
                if functools := sys.modules.get("functools"):
                    # Iterate over a copy as we will mutate the original
                    for k, v in ns.copy().items():
                        if isinstance(v, functools.cached_property):
                            cached_properties[k] = v
                            del ns[k]
                            # Add to slots only if it is not already a slot
                            slot_attrib = base_attribs.get(k, NOTHING)
                            if (
                                slot_attrib is NOTHING
                                or type(slot_attrib) not in existing_slot_types
                            ):
                                slot_values[k] = None

            # Place slots *after* everything else to be safe
            ns["__slots__"] = slot_values

            # Place pre-gathered field data - modifications are already applied
            modifications = {}
            ns[GATHERED_DATA] = fields, modifications

            new_cls = super().__new__(cls, name, bases, ns, **kwargs)

            # Now reconstruct cached properties
            if cached_properties:
                # Now the class and slots have been created, create any new cached properties
                for name, prop in cached_properties.items():
                    # This may be inherited, which is fine
                    slot = getattr(new_cls, name)

                    # May be a replaced cached property already, if so extract the actual slot
                    if isinstance(slot, _SlottedCachedProperty):
                        slot = slot.slot

                    slotted_property = _SlottedCachedProperty(
                        slot=slot,
                        func=prop.func,
                        attrname=name,
                    )

                    setattr(new_cls, name, slotted_property)

        else:
            if gatherer is not None:
                ns[META_GATHERER_NAME] = gatherer

            new_cls = super().__new__(cls, name, bases, ns, **kwargs)

        return new_cls


# This class is set up before fields as it will be used to generate the Fields
# for Field itself so Field can have generated __eq__, __repr__ and other methods
class GatheredFields:
    """
    Helper class to store gathered field data
    """

    __slots__ = ("fields", "modifications")

    def __init__(self, fields, modifications):
        self.fields = fields
        self.modifications = modifications

    def __eq__(self, other):
        if type(self) is type(other):
            return (
                self.fields == other.fields
                and self.modifications == other.modifications
            )
        return NotImplemented

    def __repr__(self):
        return f"{type(self).__name__}(fields={self.fields!r}, modifications={self.modifications!r})"

    def __call__(self, cls_or_ns):
        # cls_or_ns will be provided, but isn't needed
        return self.fields, self.modifications


# The Field class can finally be defined.
# The __init__ method has to be written manually so Fields can be created
# However after this, the other methods can be generated.
class Field(metaclass=SlotMakerMeta):
    """
    A basic class to handle the assignment of defaults/factories with
    some metadata.

    Intended to be extendable by subclasses for additional features.

    Note: When run under `pytest`, Field instances are Frozen.

    When subclassing, passing `frozen=True` will make your subclass frozen.

    :param default: Standard default value to be used for attributes with this field.
    :param default_factory: A zero-argument function to be called to generate a
                            default value, useful for mutable obects like lists.
    :param type: The type of the attribute to be assigned by this field.
    :param doc: The documentation for the attribute that appears when calling
                help(...) on the class. (Only in slotted classes).
    :param init: Include in the class __init__ parameters.
    :param repr: Include in the class __repr__.
    :param compare: Include in the class __eq__.
    :param kw_only: Make this a keyword only parameter in __init__.
    """

    # Plain slots are required as part of bootstrapping
    # This prevents SlotMakerMeta from trying to generate 'Field's
    __slots__ = (
        "default",
        "default_factory",
        "_type",
        "doc",
        "init",
        "repr",
        "compare",
        "kw_only",
    )

    # noinspection PyShadowingBuiltins
    def __init__(
        self,
        *,
        default=NOTHING,
        default_factory=NOTHING,
        type=NOTHING,
        doc=None,
        init=True,
        repr=True,
        compare=True,
        kw_only=False,
    ):
        # The init function for 'Field' cannot be generated
        # as 'Field' needs to exist first.
        # repr and comparison functions are generated as these
        # do not need to exist to create initial Fields.

        self.default = default
        self.default_factory = default_factory
        self.type = type
        self.doc = doc

        self.init = init
        self.repr = repr
        self.compare = compare
        self.kw_only = kw_only

        self.validate_field()

    def __init_subclass__(cls, frozen=False, ignore_annotations=False):
        # Subclasses of Field can be created as if they are dataclasses
        field_methods = {_field_init_maker, repr_maker, eq_maker, _field_replace_maker}
        if frozen or _UNDER_TESTING:
            field_methods |= {frozen_setattr_maker, frozen_delattr_maker}

        builder(
            cls,
            gatherer=unified_gatherer,
            methods=field_methods,
            flags={
                "slotted": True,
                "kw_only": True,
                "frozen": frozen or _UNDER_TESTING,
                "ignore_annotations": ignore_annotations,
            },
        )

    def validate_field(self):
        cls_name = self.__class__.__name__
        if (
            type(self.default) is not _NothingType
            and type(self.default_factory) is not _NothingType
        ):
            raise AttributeError(
                f"{cls_name} cannot define both a default value and a default factory."
            )

    @classmethod
    def from_field(cls, fld, /, **kwargs):
        """
        Create an instance of field or subclass from another field.

        This is intended to be used to convert a base
        Field into a subclass.

        :param fld: field class to convert
        :param kwargs: Additional keyword arguments for subclasses
        :return: new field subclass instance
        """
        # type is special cased to get the internal value
        inst_fields = {
            k: getattr(fld, k) if k != "type" else getattr(fld, "_type")
            for k in get_fields(type(fld))
        }
        argument_dict = {**inst_fields, **kwargs}

        return cls(**argument_dict)

    @property
    def type(self):
        return resolve_type(self._type)

    @type.setter
    def type(self, value):
        try:
            self._type = value
        except TypeError:
            # Under testing, frozen logic will prevent writing to _test
            object.__setattr__(self, "_type", value)

    @type.deleter
    def type(self):
        del self._type


def _build_field():
    # Complete the construction of the Field class
    field_docs = {
        "default": "Standard default value to be used for attributes with this field.",
        "default_factory":
            "A zero-argument function to be called to generate a default value, "
            "useful for mutable obects like lists.",
        "type": "The type of the attribute to be assigned by this field.",
        "doc":
            "The documentation for the attribute that appears when calling "
            "help(...) on the class. (Only in slotted classes).",
        "init": "Include this attribute in the class __init__ parameters.",
        "repr": "Include this attribute in the class __repr__",
        "compare": "Include this attribute in the class __eq__ method",
        "kw_only": "Make this a keyword only parameter in __init__",
    }  # fmt: skip

    # Fields here must be marked as kw_only to prevent the builder from trying
    # to call the __replace__ method which doesn't exist yet
    fields = {
        "default": Field(default=NOTHING, doc=field_docs["default"], kw_only=True),
        "default_factory": Field(
            default=NOTHING, doc=field_docs["default_factory"], kw_only=True
        ),
        "type": Field(default=NOTHING, doc=field_docs["type"], kw_only=True),
        "doc": Field(default=None, doc=field_docs["doc"], kw_only=True),
        "init": Field(default=True, doc=field_docs["init"], kw_only=True),
        "repr": Field(default=True, doc=field_docs["repr"], kw_only=True),
        "compare": Field(default=True, doc=field_docs["compare"], kw_only=True),
        "kw_only": Field(default=False, doc=field_docs["kw_only"], kw_only=True),
    }
    modifications = {"__slots__": field_docs}

    field_methods = {repr_maker, eq_maker, _field_replace_maker}
    if _UNDER_TESTING:
        field_methods |= {frozen_setattr_maker, frozen_delattr_maker}

    builder(
        Field,
        gatherer=GatheredFields(fields, modifications),
        methods=field_methods,
        flags={"slotted": True, "kw_only": True, "frozen": _UNDER_TESTING},
    )


_build_field()
del _build_field


def make_slot_gatherer(field_type=Field):
    """
    Create a new annotation gatherer that will work with `Field` instances
    of the creators definition.

    :param field_type: The `Field` classes to be used when gathering fields
    :return: A slot gatherer that will check for and generate Fields of
             the type field_type.
    """

    def field_slot_gatherer(cls_or_ns):
        """
        Gather field information for class generation based on __slots__

        :param cls_or_ns: Class to gather field information from (or class namespace)
        :return: dict of field_name: Field(...) and modifications to be performed by the builder
        """
        if isinstance(cls_or_ns, (_MappingProxyType, dict)):
            cls_dict = cls_or_ns
        else:
            cls_dict = cls_or_ns.__dict__

        try:
            cls_slots = cls_dict["__slots__"]
        except KeyError:
            raise AttributeError(
                "__slots__ must be defined as an instance of SlotFields "
                "in order to generate a slotclass"
            )

        if not isinstance(cls_slots, SlotFields):
            raise TypeError(
                "__slots__ must be an instance of SlotFields "
                "in order to generate a slotclass"
            )

        cls_fields = {}
        slot_replacement = {}

        for k, v in cls_slots.items():
            # Special case __dict__ and __weakref__
            # They should be included in the final `__slots__`
            # But ignored as a value.
            if k in {"__dict__", "__weakref__"}:
                slot_replacement[k] = None
                continue

            if isinstance(v, field_type):
                attrib = v
            else:
                # Plain values treated as defaults
                attrib = field_type(default=v)

            slot_replacement[k] = attrib.doc
            cls_fields[k] = attrib

        # Send the modifications to the builder for what should be changed
        # On the class.
        # In this case, slots with documentation and new annotations.
        modifications = {
            "__slots__": slot_replacement,
        }

        return cls_fields, modifications

    return field_slot_gatherer


def make_annotation_gatherer(
    field_type=Field,
    leave_default_values=False,
):
    """
    Create a new annotation gatherer that will work with `Field` instances
    of the creators definition.

    :param field_type: The `Field` classes to be used when gathering fields
    :param leave_default_values: Set to True if the gatherer should leave
                                 default values in place as class variables.
    :return: An annotation gatherer with these settings.
    """

    def field_annotation_gatherer(cls_or_ns, *, cls_annotations=None):
        # cls_annotations are included as the unified gatherer may already have
        # obtained the annotations, this prevents the method being called twice

        if isinstance(cls_or_ns, (_MappingProxyType, dict)):
            cls = None
            cls_dict = cls_or_ns
        else:
            cls = cls_or_ns
            cls_dict = cls_or_ns.__dict__

        # This should really be dict[str, field_type] but static analysis
        # doesn't understand this.
        cls_fields: dict[str, Field] = {}
        modifications = {}

        if cls_annotations is None:
            cls_annotations = get_ns_annotations(cls_dict, cls=cls)

        kw_flag = False

        for k, v in cls_annotations.items():
            _t = resolve_type(v, stringify_forwardrefs=False)

            # Ignore ClassVar
            if is_classvar(_t):
                continue

            if _t is KW_ONLY or (isinstance(_t, str) and _t == "KW_ONLY"):
                if kw_flag:
                    raise SyntaxError("KW_ONLY sentinel may only appear once.")
                kw_flag = True
                continue

            attrib = cls_dict.get(k, NOTHING)

            if attrib is not NOTHING:
                if isinstance(attrib, field_type):
                    kw_only = attrib.kw_only or kw_flag

                    # Don't try to down convert subclass instances
                    attrib_type = type(attrib)
                    attrib = attrib_type.from_field(attrib, type=v, kw_only=kw_only)

                    if attrib.default is not NOTHING and leave_default_values:
                        modifications[k] = attrib.default
                    else:
                        # NOTHING sentinel indicates a value should be removed
                        modifications[k] = NOTHING

                elif not isinstance(attrib, _MemberDescriptorType):
                    attrib = field_type(default=attrib, type=v, kw_only=kw_flag)
                    if not leave_default_values:
                        modifications[k] = NOTHING
                else:
                    attrib = field_type(type=v, kw_only=kw_flag)
            else:
                attrib = field_type(type=v, kw_only=kw_flag)

            cls_fields[k] = attrib

        return cls_fields, modifications

    return field_annotation_gatherer


def make_field_gatherer(
    field_type=Field,
    leave_default_values=False,
):
    def field_attribute_gatherer(cls_or_ns):
        if isinstance(cls_or_ns, (_MappingProxyType, dict)):
            cls_dict = cls_or_ns
        else:
            cls_dict = cls_or_ns.__dict__

        cls_attributes = {
            k: v for k, v in cls_dict.items() if isinstance(v, field_type)
        }

        cls_modifications = {}

        for name in cls_attributes.keys():
            attrib = cls_attributes[name]
            if leave_default_values:
                cls_modifications[name] = attrib.default
            else:
                cls_modifications[name] = NOTHING

        return cls_attributes, cls_modifications

    return field_attribute_gatherer


def make_unified_gatherer(
    field_type=Field,
    leave_default_values=False,
):
    """
    Create a gatherer that will work via first slots, then
    Field(...) class attributes and finally annotations if
    no unannotated Field(...) attributes are present.

    :param field_type: The field class to use for gathering
    :param leave_default_values: leave default values in place
    :return: gatherer function
    """
    slot_g = make_slot_gatherer(field_type)
    anno_g = make_annotation_gatherer(field_type, leave_default_values)
    attrib_g = make_field_gatherer(field_type, leave_default_values)

    def field_unified_gatherer(cls_or_ns):
        if isinstance(cls_or_ns, (_MappingProxyType, dict)):
            cls_dict = cls_or_ns
            cls = None
        else:
            cls_dict = cls_or_ns.__dict__
            cls = cls_or_ns

        cls_slots = cls_dict.get("__slots__")

        if isinstance(cls_slots, SlotFields):
            return slot_g(cls_dict)

        # Get ignore_annotations flag
        ignore_annotations = (
            cls_dict.get(INTERNALS_DICT, {})
            .get("flags", {})
            .get("ignore_annotations", False)
        )

        if ignore_annotations:
            return attrib_g(cls_dict)
        else:
            # To choose between annotation and attribute gatherers
            # compare sets of names.
            cls_annotations = get_ns_annotations(cls_dict, cls=cls)
            use_annotations = True

            for k, v in cls_dict.items():
                if isinstance(v, field_type):
                    v_anno = cls_annotations.get(k, NOTHING)
                    if v_anno is NOTHING:
                        use_annotations = False
                    else:
                        _t = resolve_type(v_anno)
                        if is_classvar(_t):
                            k_type = type(v).__name__
                            raise TypeError(
                                f"{k!r} is a ClassVar, but {k_type!r} instances are not supported as ClassVars"
                            )

            if use_annotations:
                # All `Field` values have annotations, so use annotation gatherer
                # Pass the original cls_or_ns object along with the already gathered annotations

                return anno_g(cls_or_ns, cls_annotations=cls_annotations)

            return attrib_g(cls_dict)

    return field_unified_gatherer


slot_gatherer = make_slot_gatherer()
annotation_gatherer = make_annotation_gatherer()

# The unified gatherer used for slot classes must remove default
# values for slots to work correctly.
unified_gatherer = make_unified_gatherer()


def check_argument_order(cls):
    """
    Raise a SyntaxError if the argument order will be invalid for a generated
    `__init__` function.

    :param cls: class being built
    """
    fields = get_fields(cls)
    used_default = False
    for k, v in fields.items():
        if v.kw_only or (not v.init):
            continue

        if v.default is NOTHING and v.default_factory is NOTHING:
            if used_default:
                raise SyntaxError(
                    f"non-default argument {k!r} follows default argument"
                )
        else:
            used_default = True


def replace(obj, /, **changes):
    """
    Create a copy of a prefab instance with values provided to 'changes' replaced

    :param obj: built class
    :return: new built class instance with changes applied
    """
    if not build_completed(type(obj)):
        raise TypeError("replace() should be called on classbuilder class instances")
    try:
        replace_func = obj.__replace__
    except AttributeError:
        raise TypeError(f"{obj.__class__.__name__!r} does not support __replace__")

    return replace_func(**changes)


# Class Decorators
def slotclass(cls=None, /, *, methods=default_methods, syntax_check=True):
    """
    Example of class builder in action using __slots__ to find fields.

    :param cls: Class to be analysed and modified
    :param methods: MethodMakers to be added to the class
    :param syntax_check: check there are no arguments without defaults
                        after arguments with defaults.
    :return: Modified class
    """
    if not cls:
        return lambda cls_: slotclass(cls_, methods=methods, syntax_check=syntax_check)

    cls = builder(cls, gatherer=slot_gatherer, methods=methods, flags={"slotted": True, "frozen": False})

    if syntax_check:
        check_argument_order(cls)

    return cls
