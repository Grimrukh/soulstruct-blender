import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .texture import Texture
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VertexWeightMixModifier(Modifier, bpy_struct):
    """Mix the weights of two vertex groups"""

    default_weight_a: float
    """ Default weight a vertex will have if it is not in the first A vgroup

    :type: float
    """

    default_weight_b: float
    """ Default weight a vertex will have if it is not in the second B vgroup

    :type: float
    """

    invert_mask_vertex_group: bool
    """ Invert vertex group mask influence

    :type: bool
    """

    invert_vertex_group_a: bool
    """ Invert the influence of vertex group A

    :type: bool
    """

    invert_vertex_group_b: bool
    """ Invert the influence of vertex group B

    :type: bool
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

    mix_mode: str
    """ How weights from vgroup B affect weights of vgroup A

    :type: str
    """

    mix_set: str
    """ Which vertices should be affected

    :type: str
    """

    normalize: bool
    """ Normalize the resulting weights (otherwise they are only clamped within 0.0 to 1.0 range)

    :type: bool
    """

    vertex_group_a: str
    """ First vertex group name

    :type: str
    """

    vertex_group_b: str
    """ Second vertex group name

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
