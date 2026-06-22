import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ducktools.classbuilder.prefab import prefab
from ducktools.classbuilder.methods import (
    MethodMaker,

    class_init_generator,
    class_eq_generator,
    counter_to_class_generator,
    get_compare_args,

    _counter_eq_generator,
    _SimpleCache,
)


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


def test_multithreaded_cache():
    thread_count = 50

    def slow_counter_eq_generator(argcount, *, funcname="__eq__"):
        time.sleep(0.01)
        return _counter_eq_generator(argcount, funcname=funcname)

    maker = MethodMaker(
        "__eq__",
        class_eq_generator,
        cached_generator=counter_to_class_generator(
            slow_counter_eq_generator,
            get_compare_args,
        )
    )

    stats = maker.cached_generator.cache.stats

    examples = []
    for _ in range(thread_count):
        @prefab(init=False, eq=False, repr=False)
        class Example:
            a: int
            b: int

        maker.attach(Example)
        examples.append(Example)

    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(getattr, example, "__eq__")
            for example in examples
        ]
        results = set()
        for future in as_completed(futures):
            results.add(future.result())

    assert len(results) == thread_count  # All different classes
    assert stats.hits == thread_count - 1
    assert stats.misses == 1
