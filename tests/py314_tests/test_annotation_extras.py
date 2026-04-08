from ducktools.classbuilder.annotations import replace_generic_with_arg, get_func_annotations, resolve_type
from ducktools.classbuilder.prefab import InitVar

from annotationlib import ForwardRef
from typing import Annotated

from reannotate import DeferredAnnotation


class TestGenericStrip:
    def test_basic_generic(self):
        def f(a: InitVar[str]): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic is str

    def test_basic_deferred(self):
        # Add a forwardref to force the use of DeferredAnnotations
        def f(a: InitVar[str], b: undefined): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic.evaluate() is str

    def test_basic_str(self):
        # Use strings
        def f(a: "InitVar[str]"): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic == "str"

    def test_layered_generic(self):
        def f(a: InitVar[list[str]]): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic == list[str]


    def test_layered_deferred(self):
        def f(a: InitVar[list[str]], b: undefined): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic.evaluate() == list[str]

    def test_layered_string(self):
        def f(a: "InitVar[list[str]]"): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic == "list[str]"

    def test_multi_generic_annotated(self):
        def f(a: Annotated[list[str], '']): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)
        assert new_generic == list[str]

    def test_multi_generic_annotated_deferred(self):
        def f(a: Annotated[list[str], ''], b: undefined): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)
        assert new_generic.evaluate() == list[str]

    def test_multi_generic_annotated_str(self):
        def f(a: "Annotated[list[str], '']"): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)
        assert new_generic == "list[str]"

    def test_no_generic(self):
        def f(a: str): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic is str

    def test_no_generic_fr(self):
        def f(a: str, b: undefined): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic.evaluate() is str

    def test_no_generic_str(self):
        def f(a: "str"): ...

        annos = get_func_annotations(f)
        a_anno = annos['a']

        new_generic = replace_generic_with_arg(a_anno)

        assert new_generic == "str"


class TestResolveType:
    def test_resolve_type_ref(self):
        def f(a: int, b: undefined): ...

        annos = get_func_annotations(f)

        assert resolve_type(annos['a']) is int

        b_fr = resolve_type(annos['b'])
        assert isinstance(b_fr, ForwardRef)
        assert b_fr.__arg__ == "undefined"

    def test_resolve_type_str(self):
        def f(a: int, b: undefined): ...

        annos = get_func_annotations(f)

        assert resolve_type(annos['a'], stringify_forwardrefs=True) is int

        b_fr = resolve_type(annos['b'], stringify_forwardrefs=True)
        assert b_fr == "undefined"