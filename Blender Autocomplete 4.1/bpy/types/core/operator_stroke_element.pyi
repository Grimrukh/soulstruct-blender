import typing
import collections.abc
import mathutils
from .struct import Struct
from .property_group import PropertyGroup
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class OperatorStrokeElement(PropertyGroup, bpy_struct):
    is_start: bool
    """ 

    :type: bool
    """

    location: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    mouse: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    mouse_event: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    pen_flip: bool
    """ 

    :type: bool
    """

    pressure: float
    """ Tablet pressure

    :type: float
    """

    size: float
    """ Brush size in screen space

    :type: float
    """

    time: float
    """ 

    :type: float
    """

    x_tilt: float
    """ 

    :type: float
    """

    y_tilt: float
    """ 

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
