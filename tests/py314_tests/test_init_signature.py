from annotationlib import get_annotations, Format

import pytest


from ducktools.classbuilder.prefab import Prefab, prefab


# Aliases for alias test
assign_int = int
type type_str = str


@pytest.mark.parametrize(
    ["format", "expected"],
    [
        (Format.VALUE, {"return": None, "x": str, "y": int}),
        (Format.FORWARDREF, {"return": None, "x": str, "y": int}),
        (Format.STRING, {"return": "None", "x": "str", "y": "int"}),
    ]
)
def test_resolvable_annotations(format, expected):
    @prefab
    class Example:
        x: str
        y: int

    annos = get_annotations(Example.__init__, format=format)

    assert annos == expected

    class Example(Prefab):
        x: str
        y: int

    annos = get_annotations(Example.__init__, format=format)

    assert annos == expected


@pytest.mark.parametrize(
    ["format", "expected"],
    [
        (Format.VALUE, {"return": None, "x": "str", "y": "late_definition"}),
        (Format.FORWARDREF, {"return": None, "x": "str", "y": "late_definition"}),
        (Format.STRING, {"return": "None", "x": "str", "y": "late_definition"}),
    ]
)
def test_late_defined_annotations(format, expected):
    # Test where the annotation is a forwardref at processing time
    @prefab
    class Example:
        x: str
        y: late_definition

    late_definition = int

    annos = get_annotations(Example.__init__, format=format)

    assert annos == expected


@pytest.mark.parametrize(
    ["format", "expected"],
    [
        (Format.VALUE, {"return": None, "x": 'str', "y": 'list[late_definition]'}),
        (Format.FORWARDREF, {"return": None, "x": 'str', "y": 'list[late_definition]'}),
        (Format.STRING, {"return": "None", "x": "str", "y": "list[late_definition]"}),
    ]
)
def test_late_defined_contained_annotations(format, expected):
    @prefab
    class Example:
        x: str
        y: list[late_definition]

    late_definition = int

    annos = get_annotations(Example.__init__, format=format)

    assert annos == expected


@pytest.mark.parametrize(
    ["format", "expected"],
    [
        (Format.VALUE, {"return": None, "x": int, "y": type_str}),
        (Format.FORWARDREF, {"return": None, "x": int, "y": type_str}),
        (Format.STRING, {"return": "None", "x": "int", "y": "type_str"}),
    ]
)
def test_alias_defined_annotations(format, expected):
    # Test the behaviour of type aliases and regular types
    # Both names should be kept in string annotations

    @prefab
    class Example:
        x: assign_int  # type: ignore
        y: type_str

    annos = get_annotations(Example.__init__, format=format)

    assert annos == expected


@pytest.mark.parametrize(
    ["format", "expected"],
    [
        (Format.FORWARDREF, {"return": None, "x": "str", "y": "undefined"}),
        (Format.STRING, {"return": "None", "x": "str", "y": "undefined"}),
    ]
)
def test_forwardref_annotation(format, expected):
    # Test where the annotation is a forwardref at processing and analysis
    class Example(Prefab):
        x: str
        y: undefined

    annos = get_annotations(Example.__init__, format=format)

    assert annos == expected


def test_contained_string_annotation():
    class Example(Prefab):
        x: list[undefined]

    annos = get_annotations(Example.__init__, format=Format.STRING)

    assert annos == {"return": "None", "x": "list[undefined]"}


def test_forwardref_string_converted():
    # Does not raise an error with value annotations as the result has been converted to a string
    @prefab
    class Example:
        x: str
        y: undefined

    annos = get_annotations(Example.__init__, format=Format.VALUE)

    assert annos == {"return": None, 'x': "str", 'y': "undefined"}


def test_with_post_init():
    @prefab
    class Example:
        x: str
        y: list[undefined]

        def __prefab_post_init__(self, y: list[undefined] | None) -> None:
            ...

    annos_value = get_annotations(Example.__init__, format=Format.VALUE)

    annos = get_annotations(Example.__init__, format=Format.FORWARDREF)

    assert annos_value == annos

    assert annos == {
        "x": "str",
        "y": "list[undefined] | None",
        "return": None,
    }
