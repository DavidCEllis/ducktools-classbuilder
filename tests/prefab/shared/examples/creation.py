import sys
import typing
from typing import ClassVar

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from ducktools.classbuilder.prefab import prefab, attribute


@prefab
class OnlyHints:
    # Remove all 3 hints and values
    x: int
    y: int = 42
    z: str = "Apple"


@prefab
class MixedHints:
    # Remove y and z, leave x in annotations
    x: int = 2
    y: int = attribute(default=42)
    z = attribute(default="Apple")


@prefab
class AllPlainAssignment:
    # remove all 3 values
    x = attribute()
    y = attribute(default=42)
    z = attribute(default="Apple")


@prefab(iter=True, match_args=True)
class KeepDefinedMethods:
    x: int = -1
    y: int = -1

    __match_args__ = ("x",)

    def __init__(self, x=0, y=0):
        self.x = 0
        self.y = 0

    def __repr__(self):
        return "ORIGINAL REPR"

    def __eq__(self, other):
        return False

    def __iter__(self):
        yield from ["ORIGINAL ITER"]


@prefab
class IgnoreClassVars:
    # Ignore v, w, x, y and z - Include actual.
    v: ClassVar = 12
    w: "ClassVar" = 24
    x: typing.ClassVar[int] = 42
    y: ClassVar[str] = "Apple"
    z: "ClassVar[float]" = 3.14
    actual: str = "Test"


# Not testing Annotated under 3.11 or earlier
@prefab
class IgnoreAnnotatedClassVars:
    # Ignore v, w, x, y and z - Include actual.
    # Ignore v and w for python 3.10 or earlier
    # as plain classvar is an error there.
    if sys.version_info >= (3, 11):
        v: Annotated[ClassVar, "v"] = 12
        w: "Annotated[ClassVar, 'w']" = 24
    x: Annotated[typing.ClassVar[int], "x"] = 42
    y: Annotated[ClassVar[str], "y"] = "Apple"
    z: "Annotated[ClassVar[float], 'z']" = 3.14
    actual: str = "Test"


@prefab
class PositionalNotAfterKW:
    # y defines a default, but it is not in the signature so should be ignored
    # for the purpose of argument order.
    x: int
    y: int = attribute(default=0, init=False)
    z: int


@prefab
class SplitVarDef:
    # Split the definition of x over 2 lines
    # This should work the same way as defining over 1 line
    x: str
    x = "test"


@prefab
class SplitVarDefReverseOrder:
    # This should still work in the reverse order
    x = "test"
    x: str


@prefab
class SplitVarRedef:
    # This should only use the last value
    x: str = "fake_test"
    x = "test"  # noqa


@prefab
class SplitVarAttribDef:
    # x here is an attribute, but it *is* typed
    # So this should still define Y correctly.
    x: str
    x = attribute(default="test")
    y: str = "test_2"


@prefab
class HorribleMess:
    # Nobody should write a class like this, but it should still work
    x: str
    x = attribute(default="fake_test", init=False, repr=False)
    x: str = "test"  # This should override the init and repr False statements
    y: str = "test_2"
    y: str


@prefab
class CallMistakenForAttribute:
    # Check that a call to str() is no longer mistaken for an attribute call
    ignore_this = str("this is a class variable")
    use_this = attribute(default="this is an attribute")


@prefab
class ConstructInitFalse:
    # Check that a class with init=False works even without a default
    x = attribute(init=False)
