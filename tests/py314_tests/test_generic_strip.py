from ducktools.classbuilder.annotations import replace_generic_with_arg, get_func_annotations
from ducktools.classbuilder.prefab import InitVar
from typing import Annotated


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

