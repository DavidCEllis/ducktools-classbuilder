# Differences with dataclasses #

While this project doesn't intend to exactly replicate other similar
modules it's worth noting where they differ in case users get tripped up.

Prefabs don't behave quite the same (externally) as dataclasses. They are
very different internally.

This doesn't include things that haven't been implemented, and only focuses
on intentional differences. Unintentional differences may be patched
or will be added to this list.

## Functional differences ##
1. prefabs do not generate the comparison methods other than `__eq__`.
    * This isn't generally a feature I want or use, however with the tools it is easy
      to add if this is a needed feature.
1. the `as_dict` method in `prefab_classes` does *not* behave the same as 
   dataclasses' `asdict`.
    * `as_dict` does *not* deepcopy the included fields, modification of mutable
      fields in the dictionary will modify them in the original object.
    * `as_dict` does *not* recurse
      - Recursion would require knowing how other objects should be serialized.
      - dataclasses `asdict`'s recursion appears to be for handling json serialization
        prefab expects the json serializer to handle recursion.
1. dataclasses provides a `fields` function to access the underlying fields.
    * Prefab classes provide a `PREFAB_FIELDS` attribute with the field names
      in order for quick access.
    * There is also a `get_attributes` function that will return the attributes.
1. Plain `attribute(...)` declarations can be used without the use of type hints.
    * If a plain assignment is used, all assignments **must** use `attribute`.
1. Post init processing uses `__prefab_post_init__` instead of `__post_init__`
    * This is just a case of not wanting any confusion between the two.
    * `attrs` similarly does `__attrs_post_init__`.
    * `__prefab_pre_init__` can also be used to define something to run
      before the body of `__init__`.
    * If an attribute name is provided as an argument to either the pre_init
      or post_init functions the value will be passed through.
1. Unlike dataclasses, prefab classes will let you use unhashable default
   values.
    * This isn't to say that mutable defaults are a good idea in general but
      prefabs are supposed to behave like regular classes and regular classes
      let you make this mistake.
    * Usually you should use `attribute(default_factory=list)` or similar.
1. If `init` is `False` in `@prefab(init=False)` the method is still generated
   but renamed to `__prefab_init__`.
1. Slots are supported but only via declaring a class with `__slots__ = SlotFields(...)`
    * The support for slots in `attrs` and `dataclasses` involves recreating the
      class as it is not possible to effectively define `__slots__` after class 
      creation. This can cause bugs where decorators or caches hold references
      to the original class.
    * By requiring slotted classes to be declared this way `@prefab` does not
      need to create a new class so all references are still correct.
1. InitVar annotations are not supported.
    * Passing arguments to `__prefab_post_init__` is done by adding the argument
      to the method signature.
    * Assignment is automatically skipped for any such values, default factories
      will be called and passed to the post init method.
    * To exclude such values from the fields list and other magic methods set
      `exclude_field=True` as an argument to `attribute`. Such attributes are
      required to be arguments to `__prefab_post_init__`.
1. The `__repr__` method for prefabs will have a different output if it will not `eval` correctly.
    * This isn't a guarantee that the regular `__repr__` will eval, but if it is known
      that the output would not `eval` then an alternative repr is used which does not
      look like it would `eval`.
1. default_factory functions will be called if `None` is passed as an argument
    * This makes it easier to wrap the function.