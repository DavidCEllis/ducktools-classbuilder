# Most pre/post init tests are shared currently
# This is a new test for using identifiers other than 'self' as the first argument
import pytest

from ducktools.classbuilder.prefab import prefab


def test_pre_init_not_self():
    @prefab
    class PreInitNotSelf:
        x: int = 1
        y: int = 2

        def __prefab_pre_init__(this, x, y):
            if x > y:
                raise ValueError("X must be less than Y")

    ex = PreInitNotSelf(1, 2)

    with pytest.raises(ValueError):
        ex = PreInitNotSelf(2, 1)


def test_pre_init_static():
    @prefab
    class PreInitStatic:
        x: int = 1
        y: int = 2

        @staticmethod
        def __prefab_pre_init__(x, y):
            if x > y:
                raise ValueError("X must be less than Y")

    ex = PreInitStatic(1, 2)

    with pytest.raises(ValueError):
        ex = PreInitStatic(2, 1)


def test_post_init_not_self():
    @prefab
    class PostInitNotSelf:
        x: int = 1
        y: int = 2

        def __prefab_post_init__(this, x, y):
            if x > y:
                raise ValueError("X must be less than Y")

            this.x = x
            this.y = y

    ex = PostInitNotSelf(1, 2)

    with pytest.raises(ValueError):
        ex = PostInitNotSelf(2, 1)
