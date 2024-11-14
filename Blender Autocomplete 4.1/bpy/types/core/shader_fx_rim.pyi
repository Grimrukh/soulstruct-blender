import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .shader_fx import ShaderFx

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderFxRim(ShaderFx, bpy_struct):
    """Rim effect"""

    blur: bpy_prop_array[int]
    """ Number of pixels for blurring rim (set to 0 to disable)

    :type: bpy_prop_array[int]
    """

    mask_color: mathutils.Color
    """ Color that must be kept

    :type: mathutils.Color
    """

    mode: str
    """ Blend mode

    :type: str
    """

    offset: bpy_prop_array[int]
    """ Offset of the rim

    :type: bpy_prop_array[int]
    """

    rim_color: mathutils.Color
    """ Color used for Rim

    :type: mathutils.Color
    """

    samples: int
    """ Number of Blur Samples (zero, disable blur)

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
