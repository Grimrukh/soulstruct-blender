import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class OperatorOptions(bpy_struct):
    """Runtime options"""

    is_grab_cursor: bool
    """ True when the cursor is grabbed

    :type: bool
    """

    is_invoke: bool
    """ True when invoked (even if only the execute callbacks available)

    :type: bool
    """

    is_repeat: bool
    """ True when run from the 'Adjust Last Operation' panel

    :type: bool
    """

    is_repeat_last: bool
    """ True when run from the operator 'Repeat Last'

    :type: bool
    """

    use_cursor_region: bool
    """ Enable to use the region under the cursor for modal execution

    :type: bool
    """

    @classmethod
    def bl_rna_get_subclass(cls, id: str | None, default=None) -> Struct:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The RNA type or default when not found.
        :rtype: Struct
        """
        ...

    @classmethod
    def bl_rna_get_subclass_py(cls, id: str | None, default=None) -> typing.Any:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The class or default when not found.
        :rtype: typing.Any
        """
        ...
