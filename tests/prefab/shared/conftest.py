import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def example_modules():
    # Folder with test examples
    base_path = Path(__file__).parent / "examples"

    # Add test folder to path temporarily
    sys.path.append(str(base_path))
    try:
        yield
    finally:
        sys.path.remove(str(base_path))
