from io import StringIO
from textwrap import indent
from unittest.mock import patch

from ducktools.classbuilder import (
    get_methods,
    get_generated_code,
    print_generated_code,
    slotclass,
    SlotFields,
    INTERNALS_DICT,
)
from ducktools.classbuilder.prefab import attribute, get_attributes, Attribute, Prefab


class Example(Prefab):
    a: int = 42
    b: str = "Life the Universe and Everything"


def test_get_attributes():
    expected = {
        "a": attribute(default=42, type=int),
        "b": attribute(default="Life the Universe and Everything", type=str),
    }
    assert get_attributes(Example) == expected

def test_get_attributes_converts_upward():
    expected = {
        "a": attribute(default=42),
    }
    @slotclass
    class HasFields:
        __slots__ = SlotFields(a=42)

    assert get_attributes(HasFields) == expected


def test_get_attributes_not_converting_downward():
    class NewAttribute(Attribute):
        new_arg: int = 42

    class HasNewAttribute(Prefab):
        a: str = NewAttribute(default="Oh dear not again")

    expected = {
        "a": NewAttribute(default="Oh dear not again", type=str)
    }

    assert get_attributes(HasNewAttribute) == expected


def test_get_generated_code_keys():
    assert get_methods(Example).keys() == get_generated_code(Example).keys()


def test_get_generated_code_source():
    methods = get_methods(Example)
    code = get_generated_code(Example)

    assert methods == getattr(Example, INTERNALS_DICT)["methods"]

    for k in methods:
        assert methods[k].code_generator(Example) == code[k]


def test_print_generated_code():
    # Test the generated source code is actually in the output string
    output = StringIO()
    code = get_generated_code(Example)

    with patch("sys.stdout", output):
        print_generated_code(Example)

    output_text = output.getvalue()

    for ex in code.values():
        assert indent(ex.source_code, "    ") in output_text
