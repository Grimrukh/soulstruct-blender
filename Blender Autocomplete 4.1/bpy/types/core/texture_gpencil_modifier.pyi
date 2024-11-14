import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TextureGpencilModifier(GpencilModifier, bpy_struct):
    """Transform stroke texture coordinates Modifier"""

    alignment_rotation: float
    """ Additional rotation applied to dots and square strokes

    :type: float
    """

    fill_offset: mathutils.Vector
    """ Additional offset of the fill UV

    :type: mathutils.Vector
    """

    fill_rotation: float
    """ Additional rotation of the fill UV

    :type: float
    """

    fill_scale: float
    """ Additional scale of the fill UV

    :type: float
    """

    fit_method: str
    """ 

    :type: str
    """

    invert_layer_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_layers: bool
    """ Inverse filter

    :type: bool
    """

    invert_material_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_materials: bool
    """ Inverse filter

    :type: bool
    """

    invert_vertex: bool
    """ Inverse filter

    :type: bool
    """

    layer: str
    """ Layer name

    :type: str
    """

    layer_pass: int
    """ Layer pass index

    :type: int
    """

    material: Material
    """ Material used for filtering effect

    :type: Material
    """

    mode: str
    """ 

    :type: str
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    uv_offset: float
    """ Offset value to add to stroke UVs

    :type: float
    """

    uv_scale: float
    """ Factor to scale the UVs

    :type: float
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
