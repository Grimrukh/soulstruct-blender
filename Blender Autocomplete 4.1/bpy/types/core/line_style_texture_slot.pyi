import typing
import collections.abc
import mathutils
from .struct import Struct
from .texture_slot import TextureSlot
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleTextureSlot(TextureSlot, bpy_struct):
    """Texture slot for textures in a LineStyle data-block"""

    alpha_factor: float
    """ Amount texture affects alpha

    :type: float
    """

    diffuse_color_factor: float
    """ Amount texture affects diffuse color

    :type: float
    """

    mapping: str
    """ 

    :type: str
    """

    mapping_x: str
    """ 

    :type: str
    """

    mapping_y: str
    """ 

    :type: str
    """

    mapping_z: str
    """ 

    :type: str
    """

    texture_coords: str
    """ Texture coordinates used to map the texture onto the background

    :type: str
    """

    use_map_alpha: bool
    """ The texture affects the alpha value

    :type: bool
    """

    use_map_color_diffuse: bool
    """ The texture affects basic color of the stroke

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
