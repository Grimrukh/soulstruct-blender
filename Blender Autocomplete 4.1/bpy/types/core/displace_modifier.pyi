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


class DisplaceModifier(Modifier, bpy_struct):
    """Displacement modifier"""

    direction: str
    """ 

    :type: str
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    mid_level: float
    """ Material value that gives no displacement

    :type: float
    """

    space: str
    """ 

    :type: str
    """

    strength: float
    """ Amount to displace geometry

    :type: float
    """

    texture: Texture
    """ 

    :type: Texture
    """

    texture_coords: str
    """ 

    :type: str
    """

    texture_coords_bone: str
    """ Bone to set the texture coordinates

    :type: str
    """

    texture_coords_object: Object
    """ Object to set the texture coordinates

    :type: Object
    """

    uv_layer: str
    """ UV map name

    :type: str
    """

    vertex_group: str
    """ Name of Vertex Group which determines influence of modifier per point

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
