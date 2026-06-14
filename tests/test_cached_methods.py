# Tests for the cached methods to check cache hits and misses and the source
# for the pre-generated methods

from pathlib import Path

import pytest

import ducktools.classbuilder._cached_methods as _cached_methods
from ducktools.classbuilder._create_precached_methods import generate_all_caches

from ducktools.classbuilder.functions import get_methods
from ducktools.classbuilder.methods import eq_maker, repr_maker
from ducktools.classbuilder.prefab import attribute, prefab, build_prefab, Prefab, KW_ONLY

def test_cached_methods_match():
    # Test the pre-generated cache matches the source
    cached_str = generate_all_caches()

    source_file = Path(_cached_methods.__file__)
    source = source_file.read_text()

    assert cached_str == source


class TestCache:
    def get_cached_class(self):
        @prefab
        class Cached:
            a: int
            b: str
        return Cached

    def get_uncached_class(self):
        fields = [(c, attribute()) for c in "abcdefghijklmnopqrstuvwxyz"]
        UnCached = build_prefab(
            "UnCached",
            fields,
        )
        return UnCached

    def reset_caches(self):
        # Restore the eq and repr caches to their initial state
        eq_maker.cached_generator.cache.clear()
        repr_maker.cached_generator.cache.clear()

    def get_eq_repr_stats(self):
        eq_stats = eq_maker.cached_generator.cache.stats
        repr_stats = repr_maker.cached_generator.cache.stats
        return eq_stats, repr_stats

    def test_cache_hit(self):
        self.reset_caches()
        Cached = self.get_cached_class()

        # Add examples to the cache
        Cached.__eq__
        Cached.__repr__

        eq_stats, repr_stats = self.get_eq_repr_stats()

        # Get a new version of the class
        Cached = self.get_cached_class()

        assert eq_stats.hits == 0
        assert eq_stats.misses == 1
        Cached.__eq__
        assert eq_stats.hits == 1
        assert eq_stats.misses == 1

        # Not regenerated
        Cached.__eq__
        assert eq_stats.hits == 1
        assert eq_stats.misses == 1

        assert repr_stats.hits == 0
        assert repr_stats.misses == 1
        Cached.__repr__
        assert repr_stats.hits == 1
        assert repr_stats.misses == 1
        Cached.__repr__
        assert repr_stats.hits == 1
        assert repr_stats.misses == 1

    def test_cache_misses(self):
        self.reset_caches()
        UnCached = self.get_uncached_class()
        eq_stats, repr_stats = self.get_eq_repr_stats()

        assert eq_stats.hits == 0
        assert eq_stats.misses == 0
        UnCached.__eq__
        assert eq_stats.hits == 0
        assert eq_stats.misses == 1

        # Not regenerated
        UnCached.__eq__
        assert eq_stats.hits == 0
        assert eq_stats.misses == 1

        assert repr_stats.hits == 0
        assert repr_stats.misses == 0
        UnCached.__repr__
        assert repr_stats.hits == 0
        assert repr_stats.misses == 1

        UnCached.__repr__
        assert repr_stats.hits == 0
        assert repr_stats.misses == 1

    def test_cache_filled(self):
        self.reset_caches()
        UnCached1 = self.get_uncached_class()
        eq_stats, repr_stats = self.get_eq_repr_stats()
        UnCached1.__eq__
        UnCached1.__repr__

        UnCached2 = self.get_uncached_class()
        assert eq_stats.hits == 0
        assert eq_stats.misses == 1
        assert repr_stats.hits == 0
        assert repr_stats.misses == 1

        UnCached2.__eq__
        UnCached2.__repr__
        assert eq_stats.hits == 1
        assert eq_stats.misses == 1
        assert repr_stats.hits == 1
        assert repr_stats.misses == 1


class TestCachedMethodsMatch:
    # Tests that the cached methods match those that would be generated
    methods = [
        "__init__",
        "__eq__",
        "__repr__",
        "__replace__",
        "__setattr__",
        "__delattr__",
        "__hash__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "__iter__",
        "as_dict",
    ]

    @pytest.mark.parametrize("method", methods)
    def test_non_init_methods(self, method):
        @prefab(order=True, frozen=True, iter=True, dict_method=True)
        class Ex:
            a: int
            b: int
            c: int
            d: int

        maker = get_methods(Ex)[method]
        codegen = maker.code_generator(Ex, method).generate()
        cached = maker.cached_generator(Ex, method)

        assert cached is not None
        assert codegen.__code__.co_code == cached.__code__.co_code
        assert codegen.__code__.co_names == cached.__code__.co_names
        assert codegen.__code__.co_consts == cached.__code__.co_consts
        assert codegen.__code__.co_varnames == cached.__code__.co_varnames
        assert codegen.__code__.co_argcount == cached.__code__.co_argcount
        assert codegen.__code__.co_kwonlyargcount == cached.__code__.co_kwonlyargcount
        assert codegen.__globals__ == cached.__globals__
        assert codegen.__qualname__ == cached.__qualname__
        assert codegen.__annotations__ == cached.__annotations__
        assert codegen.__defaults__ == cached.__defaults__
        assert codegen.__kwdefaults__ == cached.__kwdefaults__


    @pytest.mark.parametrize("frozen", [True, False])
    @pytest.mark.parametrize("slotted", [True, False])
    def test_init_basic(self, frozen, slotted):
        method = "__init__"
        class Ex(Prefab, frozen=frozen, slots=slotted):
            a: int
            b: int
            c: int = 2
            d: int = 42

        maker = get_methods(Ex)[method]
        codegen = maker.code_generator(Ex, method).generate()
        cached = maker.cached_generator(Ex, method)

        assert cached is not None
        assert codegen.__code__.co_code == cached.__code__.co_code
        assert codegen.__code__.co_names == cached.__code__.co_names
        assert codegen.__code__.co_consts == cached.__code__.co_consts
        assert codegen.__code__.co_varnames == cached.__code__.co_varnames
        assert codegen.__code__.co_argcount == cached.__code__.co_argcount
        assert codegen.__code__.co_kwonlyargcount == cached.__code__.co_kwonlyargcount
        assert codegen.__globals__ == cached.__globals__
        assert codegen.__qualname__ == cached.__qualname__
        assert codegen.__annotations__ == cached.__annotations__
        assert codegen.__defaults__ == cached.__defaults__
        assert codegen.__kwdefaults__ == cached.__kwdefaults__


    @pytest.mark.parametrize("frozen", [True, False])
    @pytest.mark.parametrize("slotted", [True, False])
    def test_init_kwonly_end(self, frozen, slotted):
        method = "__init__"
        class Ex(Prefab, frozen=frozen, slots=slotted):
            a: int
            b: int
            c: int = 2
            _: KW_ONLY
            d: int = 42

        maker = get_methods(Ex)[method]
        codegen = maker.code_generator(Ex, method).generate()
        cached = maker.cached_generator(Ex, method)

        assert cached is not None
        assert codegen.__code__.co_code == cached.__code__.co_code
        assert codegen.__code__.co_names == cached.__code__.co_names
        assert codegen.__code__.co_consts == cached.__code__.co_consts
        assert codegen.__code__.co_varnames == cached.__code__.co_varnames
        assert codegen.__code__.co_argcount == cached.__code__.co_argcount
        assert codegen.__code__.co_kwonlyargcount == cached.__code__.co_kwonlyargcount == 1
        assert codegen.__globals__ == cached.__globals__
        assert codegen.__qualname__ == cached.__qualname__
        assert codegen.__annotations__ == cached.__annotations__
        assert codegen.__defaults__ == cached.__defaults__
        assert codegen.__kwdefaults__ == cached.__kwdefaults__


    @pytest.mark.parametrize("frozen", [True, False])
    @pytest.mark.parametrize("slotted", [True, False])
    def test_init_kwonly_middle(self, frozen, slotted):
        # This tests the difference if a kw_only parameter is defined
        # in the middle of a class.
        # The assignments should be done at the end for both cached
        # and generated __init__
        # This kind of logic will also be apparent in subclasses
        method = "__init__"
        class Ex(Prefab, frozen=frozen, slots=slotted):
            a: int
            b: int
            c: int = attribute(default=2, kw_only=True)
            d: int = 42

        maker = get_methods(Ex)[method]
        codegen = maker.code_generator(Ex, method).generate()
        cached = maker.cached_generator(Ex, method)

        assert cached is not None
        assert codegen.__code__.co_code == cached.__code__.co_code
        assert codegen.__code__.co_names == cached.__code__.co_names
        assert codegen.__code__.co_consts == cached.__code__.co_consts
        assert codegen.__code__.co_varnames == cached.__code__.co_varnames
        assert codegen.__code__.co_argcount == cached.__code__.co_argcount
        assert codegen.__code__.co_kwonlyargcount == cached.__code__.co_kwonlyargcount == 1
        assert codegen.__globals__ == cached.__globals__
        assert codegen.__qualname__ == cached.__qualname__
        assert codegen.__annotations__ == cached.__annotations__
        assert codegen.__defaults__ == cached.__defaults__
        assert codegen.__kwdefaults__ == cached.__kwdefaults__

    @pytest.mark.parametrize("frozen", [True, False])
    @pytest.mark.parametrize("slotted", [True, False])
    def test_init_base(self, frozen, slotted):
        # This tests the difference if a kw_only parameter is defined
        # in the middle of a class.
        # The assignments should be done at the end for both cached
        # and generated __init__
        # This kind of logic will also be apparent in subclasses
        method = "__init__"
        class Ex(Prefab, frozen=frozen, slots=slotted):
            a: int
            b: int
            c: int = attribute(default=2, kw_only=True)
            d: int = 42

        maker = get_methods(Ex)[method]
        codegen = maker.code_generator(Ex, method).generate()
        cached = maker.cached_generator(Ex, method)

        assert cached is not None
        assert codegen.__code__.co_code == cached.__code__.co_code
        assert codegen.__code__.co_names == cached.__code__.co_names
        assert codegen.__code__.co_consts == cached.__code__.co_consts
        assert codegen.__code__.co_varnames == cached.__code__.co_varnames
        assert codegen.__code__.co_argcount == cached.__code__.co_argcount
        assert codegen.__code__.co_kwonlyargcount == cached.__code__.co_kwonlyargcount == 1
        assert codegen.__globals__ == cached.__globals__
        assert codegen.__qualname__ == cached.__qualname__
        assert codegen.__annotations__ == cached.__annotations__
        assert codegen.__defaults__ == cached.__defaults__
        assert codegen.__kwdefaults__ == cached.__kwdefaults__

    def test_init_uncached(self):
        # Test the various options that break caching actually
        # break caching as expected
        method = "__init__"

        # default_factory
        @prefab
        class Ex:
            a: int
            b: list[int] = attribute(default_factory=list)

        maker = get_methods(Ex)[method]
        cached = maker.cached_generator(Ex, method)
        assert cached is None

        # init=False with default
        @prefab
        class Ex:
            a: int
            b: int = attribute(default=42, init=False)

        maker = get_methods(Ex)[method]
        cached = maker.cached_generator(Ex, method)
        assert cached is None

        # prefab_pre_init
        @prefab
        class Ex:
            a: int
            b: int = 42

            def __prefab_pre_init__(self):
                pass

        maker = get_methods(Ex)[method]
        cached = maker.cached_generator(Ex, method)
        assert cached is None

        # prefab_post_init
        @prefab
        class Ex:
            a: int
            b: int = 42

            def __prefab_post_init__(self):
                pass

        maker = get_methods(Ex)[method]
        cached = maker.cached_generator(Ex, method)
        assert cached is None
