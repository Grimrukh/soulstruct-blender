import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .uv_projector import UVProjector
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UVProjectModifier(Modifier, bpy_struct):
    """UV projection modifier to set UVs from a projector"""

    aspect_x: float
    """ Horizontal aspect ratio (only used for camera projectors)

    :type: float
    """

    aspect_y: float
    """ Vertical aspect ratio (only used for camera projectors)

    :type: float
    """

    projector_count: int
    """ Number of projectors to use

    :type: int
    """

    projectors: bpy_prop_collection[UVProjector]
    """ 

    :type: bpy_prop_collection[UVProjector]
    """

    scale_x: float
    """ Horizontal scale (only used for camera projectors)

    :type: float
    """

    scale_y: float
    """ Vertical scale (only used for camera projectors)

    :type: float
    """

    uv_layer: str
    """ UV map name

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
