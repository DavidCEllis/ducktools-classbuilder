# Examples of extending builders #

Here are some examples of adding specific features to classes using the tools provided
by the `ducktools.classbuilder` module.

## How can I add `<method>` to the class ##

To do this you need to write a code generator that returns source code
along with a 'globals' dictionary of any names the code needs to refer
to, or an empty dictionary if none are needed. Many methods don't require
any globals values, but it is essential for some.

### Frozen Classes ###

In order to make frozen classes you need to replace `__setattr__` and `__delattr__`

The building blocks for this are actually already included as they're used to prevent
`Field` subclass instances from being mutated when under testing.

These methods can be reused to make `slotclasses` 'frozen'.

```{literalinclude} code_examples/docs_ex05_frozen.py
```

### Iterable Classes ###

Say you want to make the class iterable, so you want to add `__iter__`.

```{literalinclude} code_examples/docs_ex03_iterable.py
```

You could also choose to yield tuples of `name, value` pairs in your implementation.

## Extending Field ##

The `Field` class can also be extended as if it is a slotclass, with annotations or
with `Field` declarations.

One notable caveat - if you want to use a `default_factory` in extending `Field` you
need to declare `default=FIELD_NOTHING` also in order for default to be ignored. This
is a special case for `Field` and is not needed in general.

```python
from ducktools.classbuilder import Field, FIELD_NOTHING

class MetadataField(Field):
    metadata: dict = Field(default=FIELD_NOTHING, default_factory=dict)
```

In regular classes the `__init__` function generator considers `NOTHING` to be an
ignored value, but for `Field` subclasses it is a valid value so `FIELD_NOTHING` is
the ignored term. This is all because `None` *is* a valid value and can't be used
as a sentinel for Fields (otherwise `Field(default=None)` couldn't work).

### Positional Only Arguments? ###

This is possible, but a little longer as we also need to modify multiple methods
along with adding a check to the builder to catch likely errors before the `__init__`
method is generated.

For simplicity this demonstration version will ignore the existence of the kw_only
parameter for fields.

```{literalinclude} code_examples/docs_ex07_posonly.py
```

### Frozen Attributes ###

Here's an implementation that allows freezing of individual attributes.

```{literalinclude} code_examples/docs_ex10_frozen_attributes.py
```

### Converters ###

Here's an implementation of basic converters that always convert when
their attribute is set.

```{literalinclude} code_examples/docs_ex08_converters.py
```

## Gatherers ##
### What about using annotations instead of `Field(init=False, ...)` ###

This seems to be a feature people keep requesting for `dataclasses`.

To implement this you need to create a new annotated_gatherer function.

> Note: Field classes will be frozen when running under pytest.
>       They should not be mutated by gatherers.
>       If you need to change the value of a field use Field.from_field(...) to make a new instance.

```{literalinclude} code_examples/docs_ex09_annotated.py
```
