import sys
from pathlib import Path


_helpers = str(Path(__file__).parent / "helpers")
sys.path.insert(0, _helpers)


collect_ignore: list[str] = []

if sys.version_info < (3, 16):
    minor_ver = sys.version_info.minor

    collect_ignore.extend(
        f"py3{i+1}_tests" for i in range(minor_ver, 16)
    )


def pytest_report_header():
    return f"virtualenv: {sys.prefix}"
