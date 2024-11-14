import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VolumeRender(bpy_struct):
    """Volume object render settings"""

    clipping: float
    """ Value under which voxels are considered empty space to optimize rendering

    :type: float
    """

    precision: str
    """ Specify volume data precision. Lower values reduce memory consumption at the cost of detail

    :type: str
    """

    space: str
    """ Specify volume density and step size in object or world space

    :type: str
    """

    step_size: float
    """ Distance between volume samples. Lower values render more detail at the cost of performance. If set to zero, the step size is automatically determined based on voxel size

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
