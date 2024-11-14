import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequenceCrop(bpy_struct):
    """Cropping parameters for a sequence strip"""

    max_x: int
    """ Number of pixels to crop from the right side

    :type: int
    """

    max_y: int
    """ Number of pixels to crop from the top

    :type: int
    """

    min_x: int
    """ Number of pixels to crop from the left side

    :type: int
    """

    min_y: int
    """ Number of pixels to crop from the bottom

    :type: int
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
