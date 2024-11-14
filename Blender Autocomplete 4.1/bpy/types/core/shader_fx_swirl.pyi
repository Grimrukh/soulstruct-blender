import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .shader_fx import ShaderFx

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderFxSwirl(ShaderFx, bpy_struct):
    """Swirl effect"""

    angle: float
    """ Angle of rotation

    :type: float
    """

    object: Object
    """ Object to determine center location

    :type: Object
    """

    radius: int
    """ Radius to apply

    :type: int
    """

    use_transparent: bool
    """ Make image transparent outside of radius

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
