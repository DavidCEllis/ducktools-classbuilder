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

# Change this name if you make heavy modifications
INTERNALS_DICT = "__classbuilder_internals__"
META_GATHERER_NAME = "__classbuilder_meta_gatherer__"
GATHERED_DATA = "__classbuilder_gathered_fields__"

# Special Cache name
REPLACE_NAME = "_classbuilder_cache_names_"

# As 'None' can be a meaningful value we need a sentinel value
# to use to show no value has been provided.
class _NothingType:
    # Repeated calls to the same nothing type should
    # return the same object
    custom: str | None

    _registry = {}  # type: ignore

    def __new__(cls, custom=None):
        # Instances with the same custom name
        # should be the same object
        inst = cls._registry.get(custom)
        if inst is None:
            inst = super().__new__(cls)
            inst.custom = custom
            cls._registry[custom] = inst
        return inst

    def __repr__(self):
        if self.custom:
            return f"<{self.custom} NOTHING Sentinel>"
        return "<NOTHING Sentinel>"


NOTHING = _NothingType()
FIELD_NOTHING = _NothingType("FIELD")


# KW_ONLY sentinel 'type' to use to indicate all subsequent attributes are
# keyword only
# noinspection PyPep8Naming
class _KW_ONLY_META(type):
    def __repr__(self):
        return "<KW_ONLY Sentinel>"


class KW_ONLY(metaclass=_KW_ONLY_META):
    """
    Sentinel Class to indicate that variables declared after
    this sentinel are to be converted to KW_ONLY arguments.
    """
