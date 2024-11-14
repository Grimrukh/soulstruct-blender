import typing
import collections.abc
import mathutils
from .struct import Struct
from .texture_slot import TextureSlot
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BrushTextureSlot(TextureSlot, bpy_struct):
    """Texture slot for textures in a Brush data-block"""

    angle: float
    """ Brush texture rotation

    :type: float
    """

    has_random_texture_angle: bool
    """ 

    :type: bool
    """

    has_texture_angle: bool
    """ 

    :type: bool
    """

    has_texture_angle_source: bool
    """ 

    :type: bool
    """

    map_mode: str
    """ 

    :type: str
    """

    mask_map_mode: str
    """ 

    :type: str
    """

    random_angle: float
    """ Brush texture random angle

    :type: float
    """

    use_rake: bool
    """ 

    :type: bool
    """

    use_random: bool
    """ 

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
