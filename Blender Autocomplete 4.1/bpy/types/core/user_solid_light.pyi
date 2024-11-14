import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UserSolidLight(bpy_struct):
    """Light used for Studio lighting in solid shading mode"""

    diffuse_color: mathutils.Color
    """ Color of the light's diffuse highlight

    :type: mathutils.Color
    """

    direction: mathutils.Vector
    """ Direction that the light is shining

    :type: mathutils.Vector
    """

    smooth: float
    """ Smooth the lighting from this light

    :type: float
    """

    specular_color: mathutils.Color
    """ Color of the light's specular highlight

    :type: mathutils.Color
    """

    use: bool
    """ Enable this light in solid shading mode

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
