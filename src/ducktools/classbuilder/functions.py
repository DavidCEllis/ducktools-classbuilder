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

from .constants import INTERNALS_DICT

def build_completed(cls):
    """
    Utility function to determine if a class has completed the construction
    process.

    :param cls: class to check
    :return: True if built, False otherwise
    """
    try:
        return cls.__dict__[INTERNALS_DICT]["build_complete"]
    except KeyError:
        return False


def get_fields(cls, *, local=False):
    """
    Utility function to gather the fields dictionary
    from the class internals.

    :param cls: generated class
    :param local: get only fields that were not inherited
    :return: dictionary of keys and Field attribute info
    """
    key = "local_fields" if local else "fields"
    try:
        return getattr(cls, INTERNALS_DICT)[key]
    except (AttributeError, KeyError):
        raise TypeError(f"{cls} is not a classbuilder generated class")


def get_flags(cls):
    """
    Utility function to gather the flags dictionary
    from the class internals.

    :param cls: generated class
    :return: dictionary of keys and flag values
    """
    try:
        return getattr(cls, INTERNALS_DICT)["flags"]
    except (AttributeError, KeyError):
        raise TypeError(f"{cls} is not a classbuilder generated class")


def get_methods(cls):
    """
    Utility function to gather the set of methods
    from the class internals.

    :param cls: generated class
    :return: dict of generated methods attached to the class by name
    """
    try:
        return getattr(cls, INTERNALS_DICT)["methods"]
    except (AttributeError, KeyError):
        raise TypeError(f"{cls} is not a classbuilder generated class")


def get_generated_code(cls):
    """
    Retrieve the source code, globals and annotations of all generated methods
    as they would be generated for a specific class.

    :param cls: generated class
    :return: dict of generated method names and the GeneratedCode objects for the class
    """
    methods = get_methods(cls)
    source = {name: method.code_generator(cls) for name, method in methods.items()}

    return source


def print_generated_code(cls):
    """
    Print out all of the generated source code that will be executed for this class

    This function is useful when checking that your code generators are writing source
    code as expected.

    :param cls: generated class
    """
    import textwrap

    source = get_generated_code(cls)

    source_list = []
    globs_list = []
    annotation_list = []

    for name, method in sorted(source.items()):
        source_list.append(method.source_code)
        if method.globs:
            globs_list.append(f"{name}: {method.globs}")
        if method.annotations:
            annotation_list.append(f"{name}: {method.annotations}")

    print("Source:")
    print(textwrap.indent("\n".join(source_list), "    "))
    if globs_list:
        print("\nGlobals:")
        print(textwrap.indent("\n".join(globs_list), "    "))
    if annotation_list:
        print("\nAnnotations:")
        print(textwrap.indent("\n".join(annotation_list), "    "))
