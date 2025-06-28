import sys
import pytest

graalpy_fails = pytest.mark.xfail(
    condition=sys.implementation.name == "graalpy",
    reason="GraalPy does not support mappings in __slots__, it converts them to lists."
)
