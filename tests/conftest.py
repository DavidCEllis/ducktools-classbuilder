import sys

collect_ignore = []

if sys.version_info < (3, 15):
    minor_ver = sys.version_info.minor

    collect_ignore.extend(
        f"py3{i+1}_tests" for i in range(minor_ver, 15)
    )
