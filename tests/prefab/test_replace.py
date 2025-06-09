from __future__ import annotations

import copy
import sys

import pytest

from ducktools.classbuilder.prefab import (
    Prefab, 
    attribute, 
    prefab, 
    replace as prefab_replace,
)


replace_funcs = [prefab_replace]
if sys.version_info >= (3, 13):  # 3.13 test against the copy version too
    replace_funcs.append(copy.replace)  # type: ignore


def ex_classes() -> tuple[type, type]:
    @prefab
    class ExDecorator:
        a: int = 1
        b: str = "Why?"
        c: str = attribute(default="Non-replacable", init=False)

    class ExBaseClass(Prefab):
        a: int = 1
        b: str = "Why?"
        c: str = attribute(default="Non-replacable", init=False)

    return ExDecorator, ExBaseClass

example_classes = ex_classes()


@pytest.mark.parametrize("replace", replace_funcs)
@pytest.mark.parametrize("ex_class", example_classes)
def test_replace_decorator(ex_class, replace):
    ex = ex_class()

    assert ex.a == 1
    assert ex.b == "Why?"
    assert ex.c == "Non-replacable"

    ex_r = replace(ex, a=42)

    assert ex != ex_r

    assert ex_r.a == 42
    assert ex_r.b == "Why?"
    assert ex_r.c == "Non-replacable"


@pytest.mark.parametrize("replace", replace_funcs)
@pytest.mark.parametrize("ex_class", example_classes)
def test_replace_fail(ex_class, replace):
    ex = ex_class()

    with pytest.raises(TypeError):
        replace(ex, c="Fails")

    with pytest.raises(TypeError):
        replace(ex, d="Does Not Exist")
