import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .texture import Texture
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VolumeDisplaceModifier(Modifier, bpy_struct):
    strength: float
    """ Strength of the displacement

    :type: float
    """

    texture: Texture
    """ 

    :type: Texture
    """

    texture_map_mode: str
    """ 

    :type: str
    """

    texture_map_object: Object
    """ Object to use for texture mapping

    :type: Object
    """

    texture_mid_level: mathutils.Vector
    """ Subtracted from the texture color to get a displacement vector

    :type: mathutils.Vector
    """

    texture_sample_radius: float
    """ Smaller values result in better performance but might cut off the volume

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
