import builtins

from ducktools.classbuilder.annotations import (
    _StringGlobs,
    eval_hint,
    get_ns_annotations,
    is_classvar,
)
from typing import List, ClassVar
from typing_extensions import Annotated


def test_string_globs():
    context = _StringGlobs({'str': str})
    assert context['str'] == str
    assert context['forwardref'] == 'forwardref'

    assert repr(context) == f"_StringGlobs({{'str': {str!r}}})"


class TestEvalHint:
    def test_basic(self):
        assert eval_hint('str') == str
        assert eval_hint("'str'") == str

        assert eval_hint('forwardref') == 'forwardref'

    def test_container(self):
        context = _StringGlobs({
            **vars(builtins),
            **globals(),
            **locals()
        })

        assert eval_hint("List[str]", context) == List[str]
        assert eval_hint("ClassVar[str]", context) == ClassVar[str]

        assert eval_hint("List[forwardref]", context) == List["forwardref"]
        assert eval_hint("ClassVar[forwardref]", context) == ClassVar["forwardref"]

    def test_loop(self):
        # Check the 'seen' test prevents an infinite loop

        alt_str = str
        bleh = "bleh"

        context = _StringGlobs({
            **vars(builtins),
            **globals(),
            **locals()
        })

        assert eval_hint("alt_str", context) == str
        assert eval_hint("bleh", context) == "bleh"

    def test_evil_hint(self):
        # Nobody should evaluate anything that does this, but it shouldn't break
        # On every evaluation this function generates a new string
        # This hits the (low) recursion limit and returns the original string
        class EvilLookup:
            counter = 0

            def __getattr__(self, key):
                EvilLookup.counter += 1
                return f"EvilLookup().loop{self.counter}"

        evil_value = EvilLookup()

        context = _StringGlobs({
            **vars(builtins),
            **globals(),
            **locals()
        })

        assert eval_hint("evil_value.loop", context) == "evil_value.loop"


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
        j: "CV[str]"  # Limitation, can't see closure variables.

    annos = get_ns_annotations(vars(AnnotatedClass))

    assert annos == {
        'a': str,
        'b': str,
        'c': List[str],
        'd': List[str],
        'e': ClassVar[str],
        'f': ClassVar[str],
        'g': ClassVar['forwardref'],
        'h': Annotated[ClassVar[str], ''],
        'i': Annotated[ClassVar['forwardref'], ''],
        'j': "CV[str]",
    }


def test_is_classvar():
    assert is_classvar(ClassVar)
    assert is_classvar(ClassVar[str])
    assert is_classvar(ClassVar['forwardref'])

    assert is_classvar(Annotated[ClassVar[str], ''])
    assert is_classvar(Annotated[ClassVar['forwardref'], ''])

    assert not is_classvar(str)
    assert not is_classvar(Annotated[str, ''])
