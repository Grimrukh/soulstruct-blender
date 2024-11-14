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


class VertexWeightProximityModifier(Modifier, bpy_struct):
    """Set the weights of vertices in a group from a target object's distance"""

    falloff_type: str
    """ How weights are mapped to their new values

    :type: str
    """

    invert_falloff: bool
    """ Invert the resulting falloff weight

    :type: bool
    """

    invert_mask_vertex_group: bool
    """ Invert vertex group mask influence

    :type: bool
    """

    map_curve: CurveMapping
    """ Custom mapping curve

    :type: CurveMapping
    """

    mask_constant: float
    """ Global influence of current modifications on vgroup

    :type: float
    """

    mask_tex_map_bone: str
    """ Which bone to take texture coordinates from

    :type: str
    """

    mask_tex_map_object: Object
    """ Which object to take texture coordinates from

    :type: Object
    """

    mask_tex_mapping: str
    """ Which texture coordinates to use for mapping

    :type: str
    """

    mask_tex_use_channel: str
    """ Which texture channel to use for masking

    :type: str
    """

    mask_tex_uv_layer: str
    """ UV map name

    :type: str
    """

    mask_texture: Texture
    """ Masking texture

    :type: Texture
    """

    mask_vertex_group: str
    """ Masking vertex group name

    :type: str
    """

    max_dist: float
    """ Distance mapping to weight 1.0

    :type: float
    """

    min_dist: float
    """ Distance mapping to weight 0.0

    :type: float
    """

    normalize: bool
    """ Normalize the resulting weights (otherwise they are only clamped within 0.0 to 1.0 range)

    :type: bool
    """

    proximity_geometry: set[str]
    """ Use the shortest computed distance to target object's geometry as weight

    :type: set[str]
    """

    proximity_mode: str
    """ Which distances to target object to use

    :type: str
    """

    target: Object
    """ Object to calculate vertices distances from

    :type: Object
    """

    vertex_group: str
    """ Vertex group name

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
