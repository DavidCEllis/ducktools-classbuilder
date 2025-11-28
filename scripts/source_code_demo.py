from pathlib import Path

from ducktools.classbuilder import print_generated_code
from ducktools.classbuilder.prefab import Prefab, attribute


class Example(Prefab, order=True, iter=True, frozen=True, dict_method=True, recursive_repr=True):
    the_answer: int = 42
    the_question: str = attribute(
        default="What do you get if you multiply six by nine?",
        doc="Life the universe and everything",
    )
    python_path: Path = Path("/usr/bin/python")

print_generated_code(Example)
