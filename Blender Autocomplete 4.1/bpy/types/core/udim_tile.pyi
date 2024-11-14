import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UDIMTile(bpy_struct):
    """Properties of the UDIM tile"""

    channels: int
    """ Number of channels in the tile pixels buffer

    :type: int
    """

    generated_color: bpy_prop_array[float]
    """ Fill color for the generated image

    :type: bpy_prop_array[float]
    """

    generated_height: int
    """ Generated image height

    :type: int
    """

    generated_type: str
    """ Generated image type

    :type: str
    """

    generated_width: int
    """ Generated image width

    :type: int
    """

    label: str
    """ Tile label

    :type: str
    """

    number: int
    """ Number of the position that this tile covers

    :type: int
    """

    size: bpy_prop_array[int]
    """ Width and height of the tile buffer in pixels, zero when image data can't be loaded

    :type: bpy_prop_array[int]
    """

    use_generated_float: bool
    """ Generate floating-point buffer

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
