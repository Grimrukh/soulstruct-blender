import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VolumeGrid(bpy_struct):
    """3D volume grid"""

    channels: int
    """ Number of dimensions of the grid data type

    :type: int
    """

    data_type: str
    """ Data type of voxel values

    :type: str
    """

    is_loaded: bool
    """ Grid tree is loaded in memory

    :type: bool
    """

    matrix_object: mathutils.Matrix
    """ Transformation matrix from voxel index to object space

    :type: mathutils.Matrix
    """

    name: str
    """ Volume grid name

    :type: str
    """

    def load(self) -> bool:
        """Load grid tree from file

        :return: True if grid tree was successfully loaded
        :rtype: bool
        """
        ...

    def unload(self):
        """Unload grid tree and voxel data from memory, leaving only metadata"""
        ...

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
