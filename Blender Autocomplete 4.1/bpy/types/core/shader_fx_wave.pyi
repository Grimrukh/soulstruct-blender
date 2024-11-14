import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .shader_fx import ShaderFx

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderFxWave(ShaderFx, bpy_struct):
    """Wave Deformation effect"""

    amplitude: float
    """ Amplitude of Wave

    :type: float
    """

    orientation: str
    """ Direction of the wave

    :type: str
    """

    period: float
    """ Period of Wave

    :type: float
    """

    phase: float
    """ Phase Shift of Wave

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
