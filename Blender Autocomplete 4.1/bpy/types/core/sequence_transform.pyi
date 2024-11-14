import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequenceTransform(bpy_struct):
    """Transform parameters for a sequence strip"""

    filter: str
    """ Type of filter to use for image transformation

    :type: str
    """

    offset_x: float
    """ Move along X axis

    :type: float
    """

    offset_y: float
    """ Move along Y axis

    :type: float
    """

    origin: bpy_prop_array[float]
    """ Origin of image for transformation

    :type: bpy_prop_array[float]
    """

    rotation: float
    """ Rotate around image center

    :type: float
    """

    scale_x: float
    """ Scale along X axis

    :type: float
    """

    scale_y: float
    """ Scale along Y axis

    :type: float
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
