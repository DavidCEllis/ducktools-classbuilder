import pytest
import sys


@pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason="Module is importable under 3.10 or later"
)
def test_module_not_importable():
    with pytest.raises(ImportError):
        import ducktools.classbuilder.extras
