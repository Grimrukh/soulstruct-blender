import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .color_ramp import ColorRamp

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ColorMapping(bpy_struct):
    """Color mapping settings"""

    blend_color: mathutils.Color
    """ Blend color to mix with texture output color

    :type: mathutils.Color
    """

    blend_factor: float
    """ 

    :type: float
    """

    blend_type: str
    """ Mode used to mix with texture output color

    :type: str
    """

    brightness: float
    """ Adjust the brightness of the texture

    :type: float
    """

    color_ramp: ColorRamp
    """ 

    :type: ColorRamp
    """

    contrast: float
    """ Adjust the contrast of the texture

    :type: float
    """

    saturation: float
    """ Adjust the saturation of colors in the texture

    :type: float
    """

    use_color_ramp: bool
    """ Toggle color ramp operations

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
