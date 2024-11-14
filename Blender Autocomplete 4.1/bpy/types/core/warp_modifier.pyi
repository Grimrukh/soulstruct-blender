import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_mapping import CurveMapping
from .object import Object
from .texture import Texture
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WarpModifier(Modifier, bpy_struct):
    """Warp modifier"""

    bone_from: str
    """ Bone to transform from

    :type: str
    """

    bone_to: str
    """ Bone defining offset

    :type: str
    """

    falloff_curve: CurveMapping
    """ Custom falloff curve

    :type: CurveMapping
    """

    falloff_radius: float
    """ Radius to apply

    :type: float
    """

    falloff_type: str
    """ 

    :type: str
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    object_from: Object
    """ Object to transform from

    :type: Object
    """

    object_to: Object
    """ Object to transform to

    :type: Object
    """

    strength: float
    """ 

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

    use_volume_preserve: bool
    """ Preserve volume when rotations are used

    :type: bool
    """

    uv_layer: str
    """ UV map name

    :type: str
    """

    vertex_group: str
    """ Vertex group name for modulating the deform

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
