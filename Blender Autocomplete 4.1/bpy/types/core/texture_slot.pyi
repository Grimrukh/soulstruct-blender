import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .texture import Texture

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TextureSlot(bpy_struct):
    """Texture slot defining the mapping and influence of a texture"""

    blend_type: str
    """ Mode used to apply the texture

    :type: str
    """

    color: mathutils.Color
    """ Default color for textures that don't return RGB or when RGB to intensity is enabled

    :type: mathutils.Color
    """

    default_value: float
    """ Value to use for Ref, Spec, Amb, Emit, Alpha, RayMir, TransLu and Hard

    :type: float
    """

    name: str
    """ Texture slot name

    :type: str
    """

    offset: mathutils.Vector
    """ Fine tune of the texture mapping X, Y and Z locations

    :type: mathutils.Vector
    """

    output_node: str
    """ Which output node to use, for node-based textures

    :type: str
    """

    scale: mathutils.Vector
    """ Set scaling for the texture's X, Y and Z sizes

    :type: mathutils.Vector
    """

    texture: Texture
    """ Texture data-block used by this texture slot

    :type: Texture
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
