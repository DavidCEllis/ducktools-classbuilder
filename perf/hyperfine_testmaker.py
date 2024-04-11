"""
This script makes all of the hyperfine tests used in this project
"""
import sys
from pathlib import Path
from ducktools.classbuilder.prefab import prefab

base_dir = Path(__file__).parent / 'hyperfine_testfiles'
importer_dir = base_dir / 'hyperfine_importers'
classdef_dir = importer_dir / 'class_definitions'
results_dir = base_dir / 'hyperfine_results'

# Template Body Files #

standard_template = '''
class C{n}:
    def __init__(self, a, b, c, d, e):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e

    def __repr__(self):
        return f'C{n}({{self.a!r}}, {{self.b!r}}, {{self.c!r}}, {{self.d!r}}, {{self.e!r}})'

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return (self.a, self.b, self.c, self.d, self.e) == (other.a, other.b, other.c, other.d, other.e)
        else:
            return NotImplemented

'''

namedtuple_template = '''
C{n} = namedtuple('C{n}', ['a', 'b', 'c', 'd', 'e'])
'''

NamedTuple_template = '''
class C{n}(NamedTuple):
    a : int
    b : int
    c : int
    d : int
    e : int
'''

dataclass_template = '''
@dataclass
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int
'''

attr_noslots_template = '''
@define(slots=False)
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int
'''

attr_slots_template = '''
@define(slots=True)
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int
'''

pydantic_template = '''
class C{n}(BaseModel):
    a: int
    b: int
    c: int
    d: int
    e: int
'''

cluegen_template = '''
class C{n}(Datum):
    a: int
    b: int
    c: int
    d: int
    e: int
'''

# cluegen, but same default methods as dataclasses generated
cluegen_eval_template = '''
class C{n}(Datum):
    a: int
    b: int
    c: int
    d: int
    e: int

C{n}.__init__, C{n}.__repr__, C{n}.__eq__
'''

dataklass_template = '''
@dataklass
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int
'''

dataklass_eval_template = '''
@dataklass
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int

C{n}.__init__, C{n}.__repr__, C{n}.__eq__
'''

slotclass_template = '''
@slotclass
class C{n}:
    __slots__ = SlotFields(
        a=Field(),
        b=Field(),
        c=Field(),
        d=Field(),
        e=Field(),
    )
'''

prefab_template = '''
@prefab
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int
'''

prefab_attribute_template = '''
@prefab
class C{n}:
    a = attribute()
    b = attribute()
    c = attribute()
    d = attribute()
    e = attribute()
'''

prefab_slots_template = '''
@prefab
class C{n}:
    __slots__ = SlotFields(
        a=attribute(),
        b=attribute(),
        c=attribute(),
        d=attribute(),
        e=attribute(),
    )
'''

prefab_eval_template = '''
@prefab
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int

C{n}.__init__, C{n}.__repr__, C{n}.__eq__
'''


# Import Headings #

namedtuple_header = "from collections import namedtuple"
NamedTuple_header = "from typing import NamedTuple"
dataclass_header = "from dataclasses import dataclass"
attr_header = "from attrs import define"
pydantic_header = "from pydantic import BaseModel"
cluegen_header = "from cluegen import Datum"
dataklass_header = "from dataklasses import dataklass"
slotclass_header = "from ducktools.classbuilder import slotclass, SlotFields, Field"
prefab_header = "from ducktools.classbuilder.prefab import prefab, attribute, SlotFields"


def write_perf_file(outpath, count, template, setup):
    with open(outpath, 'w') as f:
        f.write(setup)
        for n in range(count):
            f.write(template.format(n=n))


@prefab
class TestData:
    import_name: str
    import_header: str
    class_template: str

    @property
    def importer_file(self):
        importer_name = f"{self.import_name}_timer.py"
        return importer_dir / importer_name

    @property
    def def_file(self):
        def_name = f"{self.import_name}_data.py"
        return classdef_dir / def_name

    def write_perf_importer(self):
        data = f"import class_definitions.{self.import_name}_data\n"
        self.importer_file.write_text(data)

    def write_classdef_file(self, count=100):
        with self.def_file.open(mode='w') as f:
            f.write(self.import_header)
            for n in range(count):
                f.write(self.class_template.format(n=n))


datasets = [
    TestData('native_classes', '', standard_template),
    TestData('slotclasses', slotclass_header, slotclass_template),
    TestData('prefab', prefab_header, prefab_template),
    TestData('prefab_slots', prefab_header, prefab_slots_template),
    TestData('prefab_eval', prefab_header, prefab_eval_template),
    TestData('namedtuples', namedtuple_header, namedtuple_template),
    TestData('typed_namedtuples', NamedTuple_header, NamedTuple_template),
    TestData('dataclasses', dataclass_header, dataclass_template),
    TestData('attrs_noslots', attr_header, attr_noslots_template),
    TestData('attrs_slots', attr_header, attr_slots_template),
    TestData('pydantic', pydantic_header, pydantic_template),
    # TestData('cluegen', cluegen_header, cluegen_template),
    # TestData('cluegen_eval', cluegen_header, cluegen_eval_template),
]


def write_tests(*, runs=100, warmup=20, includes_pass=True):
    base_dir.mkdir(exist_ok=True)
    importer_dir.mkdir(exist_ok=True)
    classdef_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    script_ext = "bat" if sys.platform == "win32" else "sh"

    for data in datasets:
        data.write_perf_importer()
        data.write_classdef_file(count=100)

    tests = " ".join(
        f'"python hyperfine_importers/{data.import_name}_timer.py"'
        for data in datasets
    )

    versions = (
        "import attrs, pydantic, ducktools.classbuilder;"
        "print(f'attrs {attrs.__version__}');"
        "print(f'pydantic {pydantic.__version__}');"
        "print(f'ducktools-classbuilder {ducktools.classbuilder.__version__}\\n')"
    )

    if includes_pass:
        tests = f'"python -c \\"pass\\"" {tests}'

    outpath = results_dir / 'hyperfine_result.md'

    zsh_script = (
        "python -VV\n"
        f"python -c \"{versions}\"\n"
        f"hyperfine --export-markdown {outpath} --shell=none --runs {runs} --warmup {warmup} {tests}"
    )

    shell_pth = base_dir / f"hyperfine_runner.{script_ext}"
    shell_pth.write_text(zsh_script)

    outpath = results_dir / 'hyperfine_importtimes.md'

    tests = (
        '''"python -c \\"pass\\"" '''
        '''"python -c \\"from ducktools.classbuilder import slotclass\\"" '''
        '''"python -c \\"from ducktools.classbuilder.prefab import prefab\\"" '''
        '''"python -c \\"from collections import namedtuple\\"" '''
        '''"python -c \\"from typing import NamedTuple\\"" '''
        '''"python -c \\"from dataclasses import dataclass\\"" '''
        '''"python -c \\"from attrs import define\\"" '''
        '''"python -c \\"from pydantic import BaseModel\\"" '''
    )

    import_script = (
        f"hyperfine --export-markdown {outpath} --shell=none --runs {runs} --warmup {warmup} {tests}"
    )

    shell_pth = base_dir / f'hyperfine_importtimes.{script_ext}'
    shell_pth.write_text(import_script)


if __name__ == '__main__':
    write_tests(includes_pass=True, runs=30, warmup=10)
