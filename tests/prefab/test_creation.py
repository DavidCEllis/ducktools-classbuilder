"""Tests for errors raised on class creation"""
import sys
import typing
from typing import Annotated, ClassVar

from ducktools.classbuilder.prefab import prefab, attribute
from ducktools.classbuilder.annotations import get_ns_annotations

import pytest


# These classes are defined at module level for easier 
# REPR testing
@prefab
class Empty:
    pass


@prefab
class HorribleMess:
    # Nobody should write a class like this, but it should still work
    x: str
    x = attribute(default="fake_test", init=False, repr=False)
    x: str = "test"  # type: ignore  # This should override the init and repr False statements
    y: str = "test_2"
    y: str  # type: ignore


@prefab
class ConstructInitFalse:
    # Check that a class with init=False works even without a default
    x = attribute(init=False)


@prefab
class PositionalNotAfterKW:
    # y defines a default, but it is not in the signature so should be ignored
    # for the purpose of argument order.
    x: int
    y: int = attribute(default=0, init=False)
    z: int


# Actual Tests start here
class TestEmptyClass:
    def test_empty(self):
        x = Empty()

        assert repr(x) == "Empty()"

    def test_empty_classvar(self):
        @prefab
        class EmptyClassVars:
            x: ClassVar = 12

        x = EmptyClassVars()
        assert x.x == 12
        assert "x" not in x.__dict__

    def test_empty_equal(self):
        @prefab
        class Empty:
            pass

        x = Empty()
        y = Empty()
        assert x == y

    def test_empty_iter(self):
        @prefab(iter=True)
        class EmptyIter:
            pass

        x = EmptyIter()
        lx = list(x)

        assert lx == []


class TestRemoveRecipe:
    def test_removed_defaults(self):
        @prefab
        class OnlyHints:
            # Remove all 3 hints and values
            x: int
            y: int = 42
            z: str = "Apple"

        removed_attributes = ["x", "y", "z"]
        for attrib in removed_attributes:
            assert attrib not in getattr(OnlyHints, "__dict__")
            assert attrib in get_ns_annotations(OnlyHints.__dict__)

    def test_removed_only_used_defaults(self):
        @prefab
        class MixedHints:
            # Remove y and z, leave x in annotations
            x: int = 2
            y: int = attribute(default=42)
            z = attribute(default="Apple")

        annotations = get_ns_annotations(MixedHints.__dict__)

        assert "x" in annotations
        assert "y" in annotations

        assert "x" in getattr(MixedHints, "__dict__")

        removed_attributes = ["y", "z"]
        for attrib in removed_attributes:
            assert attrib not in getattr(MixedHints, "__dict__")

    def test_removed_attributes(self):
        @prefab
        class AllPlainAssignment:
            # remove all 3 values
            x = attribute()
            y = attribute(default=42)
            z = attribute(default="Apple")

        removed_attributes = ["x", "y", "z"]
        for attrib in removed_attributes:
            assert attrib not in getattr(AllPlainAssignment, "__dict__")


class TestClassVar:
    def test_skipped_classvars(self):
        @prefab
        class IgnoreClassVars:
            # Ignore v, w, x, y and z - Include actual.
            v: ClassVar = 12
            w: "ClassVar" = 24
            x: typing.ClassVar[int] = 42
            y: ClassVar[str] = "Apple"
            z: "ClassVar[float]" = 3.14
            actual: str = "Test"

        fields = IgnoreClassVars.PREFAB_FIELDS
        assert "v" not in fields
        assert "w" not in fields
        assert "x" not in fields
        assert "y" not in fields
        assert "z" not in fields
        assert "actual" in fields

        assert "v" in getattr(IgnoreClassVars, "__dict__")
        assert "w" in getattr(IgnoreClassVars, "__dict__")
        assert "x" in getattr(IgnoreClassVars, "__dict__")
        assert "y" in getattr(IgnoreClassVars, "__dict__")
        assert "z" in getattr(IgnoreClassVars, "__dict__")

    def test_skipped_annotated_classvars(self):
        # Not testing Annotated under 3.11 or earlier
        @prefab
        class IgnoreAnnotatedClassVars:
            # Ignore v, w, x, y and z - Include actual.
            # Ignore v and w for python 3.10 or earlier
            # as plain classvar is an error there.
            if sys.version_info >= (3, 11):
                v: Annotated[ClassVar, "v"] = 12  # type: ignore
                w: "Annotated[ClassVar, 'w']" = 24  # type: ignore
            x: Annotated[typing.ClassVar[int], "x"] = 42  # type: ignore
            y: Annotated[ClassVar[str], "y"] = "Apple"  # type: ignore
            z: "Annotated[ClassVar[float], 'z']" = 3.14  # type: ignore
            actual: str = "Test"

        fields = IgnoreAnnotatedClassVars.PREFAB_FIELDS
        if sys.version_info >= (3, 11):
            assert "v" not in fields
            assert "w" not in fields
        assert "x" not in fields
        assert "y" not in fields
        assert "z" not in fields
        assert "actual" in fields

        if sys.version_info >= (3, 11):
            assert "v" in getattr(IgnoreAnnotatedClassVars, "__dict__")
            assert "w" in getattr(IgnoreAnnotatedClassVars, "__dict__")
        assert "x" in getattr(IgnoreAnnotatedClassVars, "__dict__")
        assert "y" in getattr(IgnoreAnnotatedClassVars, "__dict__")
        assert "z" in getattr(IgnoreAnnotatedClassVars, "__dict__")


class TestSplitVarDef:
    # Tests for a split variable definition
    def test_splitvardef(self):
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
            x: str  # type: ignore

        @prefab
        class SplitVarRedef:
            # This should only use the last value
            x: str = "fake_test"
            x = "test"  # noqa

        for cls in [SplitVarDef, SplitVarDefReverseOrder, SplitVarRedef]:

            assert get_ns_annotations(cls.__dict__)["x"] == str

            inst = cls()
            assert inst.x == "test"

    def test_splitvarattribdef(self):
        @prefab
        class SplitVarAttribDef:
            # x here is an attribute, but it *is* typed
            # So this should still define Y correctly.
            x: str
            x = attribute(default="test")
            y: str = "test_2"

        inst = SplitVarAttribDef()

        assert "x" in SplitVarAttribDef.PREFAB_FIELDS
        assert "y" in SplitVarAttribDef.PREFAB_FIELDS

        assert inst.x == "test"
        assert inst.y == "test_2"

    def test_horriblemess(self):
        inst = HorribleMess(x="true_test")

        assert inst.x == "true_test"
        assert repr(inst) == "HorribleMess(x='true_test', y='test_2')"

        assert get_ns_annotations(HorribleMess.__dict__) == {"x": str, "y": str}


def test_call_mistaken():
    @prefab
    class CallMistakenForAttribute:
        # Check that a call to str() is no longer mistaken for an attribute call
        ignore_this = str("this is a class variable")
        use_this = attribute(default="this is an attribute")

    # Check that ignore_this is a class variable and use_this is not
    assert CallMistakenForAttribute.ignore_this == "this is a class variable"
    assert getattr(CallMistakenForAttribute, "use_this", None) is None

    inst = CallMistakenForAttribute()
    assert inst.use_this == "this is an attribute"


class TestNonInit:
    def test_non_init_works_no_default(self):
        x = ConstructInitFalse()

        assert not hasattr(x, "x")

        x.x = 12

        assert repr(x) == "<generated class ConstructInitFalse; x=12>"

    def test_non_init_doesnt_break_syntax(self):
        # No syntax error if an attribute with a default is defined
        # before one without - if init=False for that attribute
        x = PositionalNotAfterKW(1, 2)
        assert repr(x) == "<generated class PositionalNotAfterKW; x=1, y=0, z=2>"


class TestExceptions:
    def test_positional_after_kw_error(self):
        with pytest.raises(SyntaxError) as e_info:
            @prefab
            class FailSyntax:
                x = attribute(default=0)
                y = attribute()

        assert e_info.value.args[0] == "non-default argument follows default argument"

    def test_positional_after_kw_error_factory(self):
        with pytest.raises(SyntaxError) as e_info:
            @prefab
            class FailFactorySyntax:
                x = attribute(default_factory=list)
                y = attribute()

        assert e_info.value.args[0] == "non-default argument follows default argument"

    def test_default_value_and_factory_error(self):
        """Error if defining both a value and a factory"""
        with pytest.raises(AttributeError) as e_info:
            @prefab
            class Construct:
                x = attribute(default=12, default_factory=list)

        assert (
            e_info.value.args[0]
            == "Attribute cannot define both a default value and a default factory."
        )
