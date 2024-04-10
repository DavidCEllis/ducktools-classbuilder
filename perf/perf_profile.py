# Modified from https://github.com/dabeaz/cluegen/blob/master/perf.py
# A import performance test of:
# standard classes, namedtuple, NamedTuple,
# dataclasses, attrs,
# cluegen, dataklasses,
# prefab and compiled_prefab

import os
import sys
import time
import platform

from collections import namedtuple
from typing import NamedTuple

import dataclasses
import cluegen
import dataklasses
import ducktools.classbuilder as classbuilder

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
            
C{n}.__init__, C{n}.__repr__, C{n}.__eq__
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
    
C{n}.__init__, C{n}.__repr__, C{n}.__eq__
'''

dataclass_template = '''
@dataclass
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int
    
C{n}.__init__, C{n}.__repr__, C{n}.__eq__
'''

attr_template = '''
@define
class C{n}:
    a: int
    b: int
    c: int
    d: int
    e: int
    
C{n}.__init__, C{n}.__repr__, C{n}.__eq__
'''

pydantic_template = '''
class C{n}(BaseModel):
    a: int
    b: int
    c: int
    d: int
    e: int
    
C{n}.__init__, C{n}.__repr__, C{n}.__eq__
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
@slotclass(syntax_check=True)
class C{n}:
    __slots__ = SlotFields(
        a=Field(),
        b=Field(),
        c=Field(),
        d=Field(),
        e=Field(),
    )
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


def run_test(name, n):

    import perftemp
    del sys.modules["perftemp"]

    start = time.time()
    while n > 0:
        import perftemp
        del sys.modules['perftemp']
        n -= 1
    end = time.time()
    print(f"| {name} | {end - start:.2f} |")


def write_perftemp(count, template, setup):
    with open('../perf/perftemp.py', 'w') as f:
        f.write(setup)
        for n in range(count):
            f.write(template.format(n=n))


def main(reps, test_everything=False):
    """

    :param reps: Number of repeat imports
    :param test_everything: test against dataclasses/attrs/pydantic/cluegen/dataklasses
    :return:
    """
    print(f"Python Version: {sys.version}")
    print(f"Classbuilder version: {classbuilder.__version__}")
    print(f"Platform: {platform.platform()}")

    print(f"Time for {reps} imports of 100 classes defined with 5 basic attributes")
    print("| Method | Total Time (seconds) |")
    print("| --- | --- |")
    write_perftemp(100, standard_template, '')
    run_test('standard classes', reps)

    if test_everything:
        write_perftemp(100, namedtuple_template, 'from collections import namedtuple\n')
        run_test('namedtuple', reps)

        write_perftemp(100, NamedTuple_template, 'from typing import NamedTuple\n')
        run_test('NamedTuple', reps)

        write_perftemp(100, dataclass_template, 'from dataclasses import dataclass\n')
        run_test('dataclasses', reps)

        try:
            import attrs
            write_perftemp(100, attr_template, 'from attrs import define\n')
            run_test(f'attrs {attrs.__version__}', reps)
        except ImportError:
            print("attrs not installed")

        try:
            import pydantic
            write_perftemp(100, pydantic_template, 'from pydantic import BaseModel\n')
            run_test(f'pydantic {pydantic.__version__}', reps)
        except ImportError:
            print("pydantic not installed")

        write_perftemp(100, cluegen_template, 'from cluegen import Datum\n')
        run_test('dabeaz/cluegen', reps)

        write_perftemp(100, cluegen_eval_template, 'from cluegen import Datum\n')
        run_test('dabeaz/cluegen_eval', reps)

        write_perftemp(100, dataklass_template, 'from dataklasses import dataklass\n')
        run_test('dabeaz/dataklasses', reps)

        write_perftemp(100, dataklass_eval_template, 'from dataklasses import dataklass\n')
        run_test('dabeaz/dataklasses_eval', reps)

    slotclass_import = "from ducktools.classbuilder import slotclass, Field, SlotFields\n"
    write_perftemp(100, slotclass_template, slotclass_import)
    run_test(f"slotclass {classbuilder.__version__}", reps)

    prefab_import = "from ducktools.classbuilder.prefab import prefab, attribute, SlotFields\n"

    write_perftemp(100, prefab_slots_template, prefab_import)
    run_test(f'prefab_slots {classbuilder.__version__}', reps)

    write_perftemp(100, prefab_template, prefab_import)
    run_test(f'prefab {classbuilder.__version__}', reps)

    write_perftemp(100, prefab_attribute_template, prefab_import)
    run_test(f'prefab_attributes {classbuilder.__version__}', reps)

    write_perftemp(100, prefab_eval_template, prefab_import)
    run_test(f'prefab_eval {classbuilder.__version__}', reps)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        reps = int(sys.argv[1])
    else:
        reps = 100
    main(reps, test_everything=True)
