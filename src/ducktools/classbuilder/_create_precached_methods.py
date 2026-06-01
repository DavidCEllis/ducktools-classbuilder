# MIT License
#
# Copyright (c) 2024-2026 David C Ellis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# This is the logic required to generate the pre-cached methods
# it is included in the package for easier testing.

from pathlib import Path

import ducktools.classbuilder as dtbuild

DEST = Path(dtbuild.__file__).parent / "_cached_methods.py"
COUNT = 11


def pre_generate_counter_cache(funcname, func, count, cache_name, extra_args=((),)):
    methods_list = []
    cache_lines_list = []

    try:
        # Clear the cache of potentially differently named functions
        func.clear_cache()
    except AttributeError:  # pragma: no cover
        pass

    for j, args in enumerate(extra_args):
        for i in range(count):
            new_args = (i, *args)

            name = f"{funcname}_{i}_{j}"
            methods_list.append(
                func(*new_args, funcname=name).source_code
            )

            cache_lines_list.append(f"    {new_args!r}: {name},")

    methods = "\n".join(methods_list)
    cache_lines = "\n".join(cache_lines_list)

    return f"{methods}\n{cache_name} = {{\n{cache_lines}\n}}\n\n"


def generate_all_caches():
    cache_lines = []
    cache_lines.append("# type: ignore\n")
    cache_lines.append("# This module is automatically generated from a script\n")
    cache_lines.append("# These methods are not used directly and so may reference globals that don't exist\n")
    cache_lines.append("# DO NOT EDIT BY HAND\n\n")

    cache_lines.append(pre_generate_counter_cache("_eq", dtbuild._counter_eq_generator, COUNT, "eq_cache"))  # type: ignore
    cache_lines.append(pre_generate_counter_cache("_repr", dtbuild._counter_repr_generator, COUNT, "repr_cache"))  # type: ignore
    cache_lines.append(pre_generate_counter_cache("_replace", dtbuild._counter_replace_generator, COUNT, "replace_cache"))  # type: ignore
    cache_lines.append(pre_generate_counter_cache("_hash", dtbuild._counter_hash_generator, COUNT, "hash_cache"))  # type: ignore
    cache_lines.append(pre_generate_counter_cache("_setattr", dtbuild._counter_frozen_setattr_generator, 1, "setattr_cache", extra_args=[(True,), (False,)]))  # type: ignore
    cache_lines.append(pre_generate_counter_cache("_delattr", dtbuild._counter_frozen_delattr_generator, 1, "delattr_cache"))  # type: ignore
    return "".join(cache_lines)


def write_precached_methods():  # pragma: no cover
    cache_text = generate_all_caches()
    with open(DEST, 'w') as f:
        f.write(cache_text)
