import sys
import runpy
from pathlib import Path

import pytest

from utils import graalpy_fails

DOC_CODE_FOLDER = Path(__file__).parents[1] / "docs" / "code_examples"


SCRIPT_FILES = sorted(DOC_CODE_FOLDER.glob("*.py"))


def idfn(p: Path):
    return p.name

@graalpy_fails
class TestDocCodeRuns():
    @pytest.mark.parametrize("demo_script", SCRIPT_FILES, ids=idfn)
    def test_script_executes(self, demo_script):
        # Test that the script runs without erroring
        runpy.run_path(str(demo_script), run_name="__main__")

    @pytest.mark.skipif(sys.version_info[:2] != (3, 14), reason="Only check outputs on latest Python")
    @pytest.mark.parametrize("demo_script", SCRIPT_FILES, ids=idfn)
    def test_script_output(self, demo_script, capsys):
        runpy.run_path(str(demo_script), run_name="__main__")
        captured = capsys.readouterr()

        expected_file = demo_script.parent / "outputs" / demo_script.with_suffix(".output").name
        expected = expected_file.read_text()

        assert captured.out == expected
