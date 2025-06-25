from types import MappingProxyType
from pprint import pp

import ducktools.classbuilder as dtbuild


# Step 1: Defining a Field subclass
class CustomField(dtbuild.Field):
    report: bool = True


# Step 2: Creating a new __fields__ gatherer
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

    for k, v in cls_fields_attrib.items():
        if isinstance(v, CustomField):
            gathered_fields[k] = v
        else:
            gathered_fields[k] = CustomField(default=v)

    # Modifications to be made to class attributes
    modifications = {
        "__fields__": None
    }

    return gathered_fields, modifications


# Check this gatherer works
class GathererTest:
    __fields__ = {
        "field_1": "First Field",
        "field_2": CustomField(default="Second Field"),
        "field_3": CustomField(default="Third Field", report=False),
    }

pp(fields_attribute_gatherer(GathererTest))


# Step 3: Define the 'report' code generator
def report_generator(cls, funcname="report"):
    fields = dtbuild.get_fields(cls)


    field_reports = []
    for name, fld in fields.items():
        if getattr(fld, "report", True):
            field_reports.append(f"{name}: {{self.{name}!r}}")
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


# View the generated code by testing on a demo class
@dtbuild.slotclass
class CodegenDemo:
    __slots__ = dtbuild.SlotFields(
        field_1="Field one",
        field_2="Field two",
        field_3="Field three",
    )


print(report_generator(CodegenDemo).source_code)


# Step 4a: Define a decorator builder
# Import the builder and method makers for eq/repr/init

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

# Step 4b: Define a base class builder
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

        slotted = "__slots__" in vars(cls)
        flags = {"slotted": slotted}

        dtbuild.builder(cls, gatherer=gatherer, methods=methods, flags=flags)


# Step 5: Examples
@reportclass
class Example:
    __fields__ = {
        "x": 42,
        "y": CustomField(default="value", report=False)
    }

print(Example().report)


class ExampleSlots(ReportClass):
    __fields__ = {
        "x": 42,
        "y": CustomField(default="value", report=False)
    }

print(ExampleSlots().report)
