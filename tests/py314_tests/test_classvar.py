"""
Test that ClassVar works if DeferredAnnotations are used
"""

import typing as t
from ducktools.classbuilder.prefab import prefab, get_attributes

class TestClassVarRef:
    def test_basic_ref(self):
        @prefab
        class Example:
            a: t.ClassVar[unknown]
            b: str

        attribs = get_attributes(Example)

        assert 'a' not in attribs
        assert 'b' in attribs

    def test_plain_classvar(self):
        # Test a plain ClassVar in a context where annotations will be
        # DeferredAnnotations (ie: there's a forwardref)
        @prefab
        class Example:
            a: t.ClassVar
            b: unknown

        attribs = get_attributes(Example)

        assert 'a' not in attribs
        assert 'b' in attribs

    def test_plain_classvar_annotated(self):
        # Test again but wrapped in Annotated
        @prefab
        class Example:
            a: t.Annotated[t.ClassVar, '']
            b: unknown

        attribs = get_attributes(Example)

        assert 'a' not in attribs
        assert 'b' in attribs

    def test_unresolvable_ref(self):
        # This tests that ClassVar still works even if the entire annotation is
        # unresolvable as a forward reference
        @prefab
        class Example:
            a: t.ClassVar[t.unresolvable]
            b: str

        attribs = get_attributes(Example)

        assert 'a' not in attribs
        assert 'b' in attribs

    def test_annotated_basic(self):
        @prefab
        class Example:
            a: t.Annotated[t.ClassVar[unknown], '']
            b: str

        attribs = get_attributes(Example)

        assert 'a' not in attribs
        assert 'b' in attribs

    def test_annotated_unresolvable(self):
        @prefab
        class Example:
            a: t.Annotated[t.ClassVar[t.unresolvable], '']
            b: str

        attribs = get_attributes(Example)

        assert 'a' not in attribs
        assert 'b' in attribs
