# Ducktools: ClassBuilder #

```{toctree}
---
maxdepth: 2
caption: "Contents:"
hidden: true
---
prefab/api
```

`ducktools-classbuilder` is *the* Python package that will bring you the *joy*
of writing *functions that write classes*...

Maybe that's just me.

The original version of this project `PrefabClasses` came about as I was getting
frustrated at the need to write converters or wrappers for multiple methods when
using `attrs`, where all I really wanted to do was coerce empty values to None 
(or the other way around).
Further development came when I started investigating CLI tools and noticed the
significant overhead of both `attrs` and `dataclasses` on import time, even before
generating any classes.


## Indices and tables ##

* {ref}`genindex`
* {ref}`search`
