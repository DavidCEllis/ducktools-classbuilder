# Pre and Post Init Methods #

Alongside the standard method generation `@prefab` decorated classes
have special behaviour if `__prefab_pre_init__` or `__prefab_post_init__`
methods are defined.

For both methods if they have additional arguments with names that match
defined attributes, the matching arguments to `__init__` will be passed
through to the method. 

**If an argument is passed to `__prefab_post_init__`it will not be initialized
in `__init__`**. It is expected that initialization will occur in the method
defined by the user.

Other than this, arguments provided to pre/post init do not modify the behaviour
of their corresponding attributes (they will still appear in the other magic
methods).

Examples have had repr and eq removed for brevity.

## Examples ##

### \_\_prefab_pre_init\_\_ ###

Input code:

```python
from ducktools.classbuilder.prefab import prefab

@prefab(repr=False, eq=False)
class ExampleValidate:
    x: int
    
    @staticmethod
    def __prefab_pre_init__(x):
        if x <= 0:
            raise ValueError("x must be a positive integer")
```

Equivalent code:

```python
class ExampleValidate:
    PREFAB_FIELDS = ['x']
    __match_args__ = ('x',)
    
    def __init__(self, x: int):
        self.__prefab_pre_init__(x=x)
        self.x = x
    
    @staticmethod
    def __prefab_pre_init__(x):
        if x <= 0:
            raise ValueError('x must be a positive integer')
```

### \_\_prefab_post_init\_\_ ###

Input code:

```python
from ducktools.classbuilder.prefab import prefab, attribute
from pathlib import Path

@prefab(repr=False, eq=False)
class ExampleConvert:
    x: Path = attribute(default='path/to/source')

    def __prefab_post_init__(self, x: Path | str):
        self.x = Path(x)
```

Equivalent code:

```python
from pathlib import Path
class ExampleConvert:
    PREFAB_FIELDS = ['x']
    __match_args__ = ('x',)
    
    x: Path
    
    def __init__(self, x: Path | str = 'path/to/source'):
        self.__prefab_post_init__(x=x)
    
    def __prefab_post_init__(self, x: Path | str):
        self.x = Path(x)
```
