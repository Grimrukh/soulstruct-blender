import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .shader_fx import ShaderFx

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderFxGlow(ShaderFx, bpy_struct):
    """Glow effect"""

    blend_mode: str
    """ Blend mode

    :type: str
    """

    glow_color: mathutils.Color
    """ Color used for generated glow

    :type: mathutils.Color
    """

    mode: str
    """ Glow mode

    :type: str
    """

    opacity: float
    """ Effect Opacity

    :type: float
    """

    rotation: float
    """ Rotation of the effect

    :type: float
    """

    samples: int
    """ Number of Blur Samples

    :type: int
    """

    select_color: mathutils.Color
    """ Color selected to apply glow

    :type: mathutils.Color
    """

    size: mathutils.Vector
    """ Size of the effect

    :type: mathutils.Vector
    """

    threshold: float
    """ Limit to select color for glow effect

    :type: float
    """

    use_glow_under: bool
    """ Glow only areas with alpha (not supported with Regular blend mode)

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
