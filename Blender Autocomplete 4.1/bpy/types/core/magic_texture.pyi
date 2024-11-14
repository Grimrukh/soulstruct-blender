import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .texture import Texture

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MagicTexture(Texture, ID, bpy_struct):
    """Procedural noise texture"""

    noise_depth: int
    """ Depth of the noise

    :type: int
    """

    turbulence: float
    """ Turbulence of the noise

    :type: float
    """

    users_material: typing.Any
    """ Materials that use this texture(readonly)"""

    users_object_modifier: typing.Any
    """ Object modifiers that use this texture(readonly)"""

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
