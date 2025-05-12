from annotationlib import ForwardRef

# From test/support/__init__.py
class EqualToForwardRef:
    """Helper to ease use of annotationlib.ForwardRef in tests.

    This checks only attributes that can be set using the constructor.

    """

    def __init__(
        self,
        arg,
        *,
        module=None,
        owner=None,
        is_class=False,
    ):
        self.__forward_arg__ = arg
        self.__forward_is_class__ = is_class
        self.__forward_module__ = module
        self.__owner__ = owner

    def __eq__(self, other):
        if not isinstance(other, (EqualToForwardRef, ForwardRef)):
            return NotImplemented
        return (
            self.__forward_arg__ == other.__forward_arg__
            and self.__forward_module__ == other.__forward_module__
            and self.__forward_is_class__ == other.__forward_is_class__
            and self.__owner__ == other.__owner__
        )

    def __repr__(self):
        extra = []
        if self.__forward_module__ is not None:
            extra.append(f", module={self.__forward_module__!r}")
        if self.__forward_is_class__:
            extra.append(", is_class=True")
        if self.__owner__ is not None:
            extra.append(f", owner={self.__owner__!r}")
        return f"EqualToForwardRef({self.__forward_arg__!r}{''.join(extra)})"
