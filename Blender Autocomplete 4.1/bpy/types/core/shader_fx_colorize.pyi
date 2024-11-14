import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .shader_fx import ShaderFx

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderFxColorize(ShaderFx, bpy_struct):
    """Colorize effect"""

    factor: float
    """ Mix factor

    :type: float
    """

    high_color: bpy_prop_array[float]
    """ Second color used for effect

    :type: bpy_prop_array[float]
    """

    low_color: bpy_prop_array[float]
    """ First color used for effect

    :type: bpy_prop_array[float]
    """

    mode: str
    """ Effect mode

    :type: str
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
