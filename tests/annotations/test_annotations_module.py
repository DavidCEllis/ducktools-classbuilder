import builtins

from ducktools.classbuilder.annotations import (
    get_ns_annotations,
    is_classvar,
)
from typing import List, ClassVar
from typing_extensions import Annotated


def test_ns_annotations():
    CV = ClassVar

    class AnnotatedClass:
        a: str
        b: "str"
        c: List[str]
        d: "List[str]"
        e: ClassVar[str]
        f: "ClassVar[str]"
        g: "ClassVar[forwardref]"
        h: "Annotated[ClassVar[str], '']"
        i: "Annotated[ClassVar[forwardref], '']"
        j: "CV[str]"

    annos = get_ns_annotations(vars(AnnotatedClass))

    assert annos == {
        'a': str,
        'b': "str",
        'c': List[str],
        'd': "List[str]",
        'e': ClassVar[str],
        'f': "ClassVar[str]",
        'g': "ClassVar[forwardref]",
        'h': "Annotated[ClassVar[str], '']",
        'i': "Annotated[ClassVar[forwardref], '']",
        'j': "CV[str]",
    }


def test_is_classvar():
    assert is_classvar(ClassVar)
    assert is_classvar(ClassVar[str])
    assert is_classvar(ClassVar['forwardref'])

    assert is_classvar(Annotated[ClassVar[str], ''])
    assert is_classvar(Annotated[ClassVar['forwardref'], ''])

    assert is_classvar("ClassVar")
    assert is_classvar("ClassVar[str]")
    assert is_classvar("ClassVar['forwardref']")

    assert is_classvar("Annotated[ClassVar[str], '']")
    assert is_classvar("Annotated[ClassVar['forwardref'], '']")

    assert not is_classvar(str)
    assert not is_classvar(Annotated[str, ''])
