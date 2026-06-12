# Tests for the cached methods to check cache hits and misses and the source
# for the pre-generated methods

from pathlib import Path

import ducktools.classbuilder._cached_methods as _cached_methods
from ducktools.classbuilder._create_precached_methods import generate_all_caches

from ducktools.classbuilder.methods import eq_maker, repr_maker
from ducktools.classbuilder.prefab import attribute, prefab, build_prefab

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
