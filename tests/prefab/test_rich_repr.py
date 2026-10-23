from ducktools.classbuilder.prefab import prefab, Prefab, attribute

from rich.pretty import pretty_repr


def test_empty_class():
    @prefab
    class Example:
        pass

    assert pretty_repr(Example()) == "Example()"


def test_basic_class():
    # Unslotted Class
    @prefab
    class Example:
        a: int
        b: int
        c: int

    ex = Example(1, 2, 3)

    assert pretty_repr(ex) == "Example(a=1, b=2, c=3)"


def test_slotted_class():
    # Slotted Class
    class Example(Prefab):
        a: int
        b: int
        c: int

    ex = Example(1, 2, 3)

    assert pretty_repr(ex) == "Example(a=1, b=2, c=3)"


def test_no_overwrite_rich_repr():
    @prefab
    class Example:
        a: int
        b: int = 42
        def __rich_repr__(self):
            # Demo repr with only positional arguments
            yield self.a
            yield self.b

    assert pretty_repr(Example(1)) == "Example(1, 42)"


def test_no_repr():
    @prefab(repr=False)
    class Example:
        a: int
        b: int

    # Only gets default repr
    assert pretty_repr(Example(1, 2)).startswith(
        "<test_rich_repr.test_no_repr.<locals>.Example"
    )


def test_defaults():
    class Example(Prefab):
        meaning: int = 42
        message: str = "So long and thanks for all the fish"

    assert pretty_repr(Example()) == "Example()"
    assert pretty_repr(Example(42, "So long and thanks for all the fish")) == "Example()"

    assert pretty_repr(Example(4)) == "Example(meaning=4)"

    assert pretty_repr(Example(message="Mostly Harmless")) == "Example(message='Mostly Harmless')"


def test_default_factory():
    @prefab
    class Example:
        names: list[str] = attribute(default_factory=list)
        mappings: dict[str, str] = attribute(default_factory=dict)

    assert pretty_repr(Example()) == "Example()"

    assert pretty_repr(Example(names=[], mappings={})) == "Example()"

    assert pretty_repr(Example(names=["Dent", "Beeblebrox"])) == "Example(names=['Dent', 'Beeblebrox'])"
    assert pretty_repr(Example(mappings={"Marvin": "Paranoid"})) == "Example(mappings={'Marvin': 'Paranoid'})"


def test_excluded():
    @prefab
    class Example:
        name: str
        private: str = attribute(repr=False)

    assert pretty_repr(Example("Skroob", "12345")) == "Example(name='Skroob')"
