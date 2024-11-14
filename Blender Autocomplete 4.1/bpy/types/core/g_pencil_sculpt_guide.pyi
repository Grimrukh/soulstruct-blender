import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilSculptGuide(bpy_struct):
    """Guides for drawing"""

    angle: float
    """ Direction of lines

    :type: float
    """

    angle_snap: float
    """ Angle snapping

    :type: float
    """

    location: bpy_prop_array[float]
    """ Custom reference point for guides

    :type: bpy_prop_array[float]
    """

    reference_object: Object
    """ Object used for reference point

    :type: Object
    """

    reference_point: str
    """ Type of speed guide

    :type: str
    """

    spacing: float
    """ Guide spacing

    :type: float
    """

    type: str
    """ Type of speed guide

    :type: str
    """

    use_guide: bool
    """ Enable speed guides

    :type: bool
    """

    use_snapping: bool
    """ Enable snapping to guides angle or spacing options

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
