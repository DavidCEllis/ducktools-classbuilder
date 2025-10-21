# This is no longer used but something similar may be needed for future python releases

import sys

if sys.version_info >= (3, 15):
    from annotationlib import ForwardRef, type_repr

    class SimpleEqualToForwardRef:
        def __init__(self, arg):
            self.__forward_arg__ = arg

        def __eq__(self, other):
            if not isinstance(other, (SimpleEqualToForwardRef, ForwardRef)):
                return NotImplemented
            else:
                return self.__forward_arg__ == other.__forward_arg__

        def __repr__(self):
            return f"SimpleEqualToForwardRef({self.__forward_arg__!r})"


    def matches_type(arg):
        if isinstance(arg, str):
            return SimpleEqualToForwardRef(arg)

        return SimpleEqualToForwardRef(type_repr(arg))
else:
    def matches_type(arg):
        return arg
