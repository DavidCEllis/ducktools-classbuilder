import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ducktools.classbuilder.prefab import prefab
from ducktools.classbuilder.methods import class_init_generator, MethodMaker


def test_multithreaded_generator():
    def slow_init_generator(cls: type, funcname: str = "__init__"):
        # A generator with a delay so multiple threads can attempt
        # to generate
        time.sleep(0.01)
        return class_init_generator(cls, funcname=funcname)

    slow_init_maker = MethodMaker("__init__", slow_init_generator)

    @prefab(init=False, eq=False, repr=False)
    class Example:
        a: int
        b: int

    slow_init_maker.attach(Example)

    get_init = lambda cls: cls.__init__

    with ThreadPoolExecutor() as pool:
        futures = [pool.submit(get_init, Example) for _ in range(50)]
        results = set()
        for future in as_completed(futures):
            results.add(future.result())

    # Assert generation has only occured once as there is only
    # one unique function in results
    assert len(results) == 1
