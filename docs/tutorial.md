# Tutorial: Making a class boilerplate generator #

The core idea is that there are 4 parts to the process of generating
the class boilerplate that need to be handled:

1. Create a new subclass of `Field` if you need to add any extra attributes to fields
2. Make a new gatherer function or use one of the tools provided to create a generator
   that will use your new `Field` subclass (ex: `make_unified_gatherer(NewField)`)
3. Write any code generator functions you wish to add or modify for your class
4. Create a function or base class that applies these to classes using the `builder` provided

The field gathering **should not** attempt to do any inheritance checking, that is already handled
by the `builder` function. `slot_gatherer` is an example of a gatherer.

To demonstrate this we will go through making a new Field, gatherer, generated method, class decorator
and base class.

## Deciding on Customizations ##

For the purpose of this tutorial we are going to make a special
class generator which works by collecting fields from a `__fields__`
attribute and will generate the usual `__init__`, `__repr__` and `__eq__`
functions alongside a new `report` method that will give a longer set of 
details about a class instance.

The input will look like this:
```python
class Example(ReportClass):
    __fields__ = {
        "x": 42,
        "y": CustomField(default="value", report=False)
    }
```

The final code from this tutorial is available in `docs_code/tutorial_code.py`

These are the imports required for all of the following steps:

```python
from types import MappingProxyType
from pprint import pp

import ducktools.classbuilder as dtbuild
```

## Step 1: Defining a Field subclass ##

The first step is to generate our new Field subclass to add the `report`
attribute that can be used to hide the value from the report if desired.

```python
class CustomField(dtbuild.Field):
    report: bool = True
```

That is it, this will now function as a field with the additional keyword only
parameter `report` added. 

## Step 2: Creating a new `__fields__` gatherer ##

Having done that we now need to create a gatherer that will collect values from `__fields__`.
After a class has been built `__fields__` will be set to None to indicate that the class has
been created and not to attempt to repeat the process.

```python
def fields_attribute_gatherer(cls_or_ns):
    # Gatherers need to work on either a class or a class namespace
    # `builder` will operate on the class while `SlotMakerMeta` only has the namespace
    if isinstance(cls_or_ns, (MappingProxyType, dict)):
        cls_dict = cls_or_ns
    else:
        cls_dict = cls_or_ns.__dict__

    cls_fields_attrib = cls_dict.get("__fields__", None)

    if cls_fields_attrib is None:
        raise AttributeError("Class has already been generated or `__fields__` has not been set")
    elif not isinstance(cls_fields_attrib, dict):
        raise TypeError("__fields__ attribute must be a dictionary")

    gathered_fields = {}

    # Field or CustomField instances will be copied and converted if needed
    # Plain values will be made into CustomField instances
    for k, v in cls_fields_attrib.items():
        if isinstance(v, dtbuild.Field):
            gathered_fields[k] = CustomField.from_field(v)
        else:
            gathered_fields[k] = CustomField(default=v)

    # Modifications to be made to class attributes
    modifications = {
        "__fields__": None
    }

    return gathered_fields, modifications
```

Demonstrate the output of this gatherer:
```python
class GathererTest:
    __fields__ = {
        "field_1": "First Field",
        "field_2": CustomField(default="Second Field"),
        "field_3": CustomField(default="Third Field", report=False),
    }

pp(fields_attribute_gatherer(GathererTest))
```

## Step 3: Define the 'report' code generator ##

For the example just demonstrated our report will generate output like this.

```
Class: GathererTest
field_1: "First Field"
field_2: "Second Field"
field_3: <HIDDEN>
```

```python
def report_generator(cls, funcname="report"):
    fields = dtbuild.get_fields(cls)

    field_reports = []
    for name, fld in fields.items():
        if getattr(fld, "report", True):
            field_reports.append(f"{name}: {{repr(self.{name})}}")
        else:
            field_reports.append(f"{name}: <HIDDEN>")

    reports_str = "\\n".join(field_reports)
    class_str = f"Class: {cls.__name__}"

    code = (
        "@property\n"
        f"def {funcname}(self):\n"
        f"    return f\"{class_str}\\n{reports_str}\""
    )
    globs = {}

    return dtbuild.GeneratedCode(code, globs)


report_maker = dtbuild.MethodMaker("report", report_generator)
```

We can take a quick look at what this generates by applying it to a `slotclass`:
```python
@dtbuild.slotclass
class CodegenDemo:
    __slots__ = dtbuild.SlotFields(
        field_1="Field one",
        field_2="Field two",
        field_3="Field three",       
    )
    field_1: str = "Field one"
    field_2: str = "Field two"
    field_3: str = "Field three"


print(report_generator(CodegenDemo).source_code)
```

## Step 4: Create the builders ##

Here we will make both a simple decorator based builder and then a subclass
based builder that can create `__slots__`.

### 4a: Decorator builder ###
```python
def reportclass(cls):
    gatherer = fields_attribute_gatherer
    methods = {
        dtbuild.eq_maker, 
        dtbuild.repr_maker, 
        dtbuild.init_maker, 
        report_maker
    }

    slotted = "__slots__" in vars(cls)
    flags = {"slotted": slotted}

    return dtbuild.builder(cls, gatherer=gatherer, methods=methods, flags=flags)
```

### 4b: Base class Builder ###
```python
# Once slots have been made, slot_gatherer should be used.
slot_gatherer = dtbuild.make_slot_gatherer(CustomField)


class ReportClass(metaclass=dtbuild.SlotMakerMeta, gatherer=fields_attribute_gatherer):
    __slots__ = {}
    
    def __init_subclass__(cls):
        # Check if the metaclass has pre-gathered data
        pre_gathered = dtbuild.GATHERED_DATA in vars(cls)
        gatherer = dtbuild.pre_gathered_gatherer if pre_gathered else fields_attribute_gatherer
        methods = {
            dtbuild.eq_maker,
            dtbuild.repr_maker,
            dtbuild.init_maker,
            report_maker
        }

        # The class may still have slots unrelated to code generation
        slotted = "__slots__" in vars(cls)
        flags = {"slotted": slotted}

        dtbuild.builder(cls, gatherer=gatherer, methods=methods, flags=flags)
```

## Step 5: Try out the new class generators and method ##

Unslotted with decorator:
```python
@reportclass
class Example:
    __fields__ = {
        "x": 42,
        "y": CustomField(default="value", report=False)
    }

print(Example().report)
```


Slotted with base class:
```python
class ExampleSlots(ReportClass):
    __fields__ = {
        "x": 42,
        "y": CustomField(default="value", report=False)
    }

print(ExampleSlots().report)
```


