import sys
import subprocess
from pathlib import Path

scriptfiles: list[Path] = sorted(Path("docs/code_examples").glob("*.py"))
outfiles: list[Path] = [f.parent / "outputs" / f.with_suffix(".output").name for f in scriptfiles]

for i, o in zip(scriptfiles, outfiles):
    result = subprocess.run([sys.executable, str(i)], capture_output=True, text=True)
    o.write_text(result.stdout)
