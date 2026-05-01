from pathlib import Path

import ducktools.classbuilder as dtbuild

DEST = Path(dtbuild.__file__).parent / "_cached_methods.py"
COUNT = 20

def pre_generate_cache(funcname, func, count, cache_name):
    methods_list = []
    cache_lines_list = []

    for i in range(count):
        name = f"{funcname}_{i}"
        methods_list.append(
            func(i, funcname=name).source_code
        )

        cache_lines_list.append(f"    ({i},): {name},")

    methods = "\n".join(methods_list)
    cache_lines = "\n".join(cache_lines_list)

    return f"{methods}\n{cache_name} = {{\n{cache_lines}\n}}\n"


def main():
    with open(DEST, 'w') as f:
        f.write("# This module is automatically generated from a script\n")
        f.write("# DO NOT EDIT BY HAND\n\n")

        f.write(pre_generate_cache("_eq", dtbuild.counter_eq_generator, COUNT, "eq_cache"))
        f.write(pre_generate_cache("_repr", dtbuild.counter_repr_generator, COUNT, "repr_cache"))

if __name__ == "__main__":
    main()
