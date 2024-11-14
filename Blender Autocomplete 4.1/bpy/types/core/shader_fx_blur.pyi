import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .shader_fx import ShaderFx

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderFxBlur(ShaderFx, bpy_struct):
    """Gaussian Blur effect"""

    rotation: float
    """ Rotation of the effect

    :type: float
    """

    samples: int
    """ Number of Blur Samples (zero, disable blur)

    :type: int
    """

    size: mathutils.Vector
    """ Factor of Blur

    :type: mathutils.Vector
    """

    use_dof_mode: bool
    """ Blur using camera depth of field

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
