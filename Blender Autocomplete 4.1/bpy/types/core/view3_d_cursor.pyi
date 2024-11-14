import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class View3DCursor(bpy_struct):
    location: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    matrix: mathutils.Matrix
    """ Matrix combining location and rotation of the cursor

    :type: mathutils.Matrix
    """

    rotation_axis_angle: bpy_prop_array[float]
    """ Angle of Rotation for Axis-Angle rotation representation

    :type: bpy_prop_array[float]
    """

    rotation_euler: mathutils.Euler
    """ 3D rotation

    :type: mathutils.Euler
    """

    rotation_mode: str
    """ 

    :type: str
    """

    rotation_quaternion: mathutils.Quaternion
    """ Rotation in quaternions (keep normalized)

    :type: mathutils.Quaternion
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
