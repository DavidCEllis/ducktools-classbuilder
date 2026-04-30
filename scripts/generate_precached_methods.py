from pathlib import Path

import ducktools.classbuilder as dtbuild

DEST = Path(dtbuild.__file__).parent / "_cached_methods.py"
COUNT = 20

def pre_generate_cache(func, count, cache_name):
    methods_list = []
    cache_lines_list = []

    for i in range(count):
        funcname = f"__eq_{i}__"
        methods_list.append(
            func(i, funcname=funcname).source_code
        )
        cache_lines_list.append(f"    ({i},): {funcname},")

    methods = "\n".join(methods_list)
    cache_lines = "\n".join(cache_lines_list)

    return f"{methods}\n{cache_name} = {{\n{cache_lines}\n}}\n"


def main():
    with open(DEST, 'w') as f:
        f.write("# This module is automatically generated from a script\n")
        f.write("# DO NOT EDIT BY HAND\n\n")

        f.write(pre_generate_cache(dtbuild.generic_eq_generator, COUNT, "eq_cache"))

if __name__ == "__main__":
    main()
