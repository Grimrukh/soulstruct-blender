import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class OffsetGpencilModifier(GpencilModifier, bpy_struct):
    """Offset Stroke modifier"""

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

    location: mathutils.Vector
    """ Values for change location

    :type: mathutils.Vector
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

    random_offset: mathutils.Vector
    """ Value for changes in location

    :type: mathutils.Vector
    """

    random_rotation: mathutils.Euler
    """ Value for changes in rotation

    :type: mathutils.Euler
    """

    random_scale: mathutils.Vector
    """ Value for changes in scale

    :type: mathutils.Vector
    """

    rotation: mathutils.Euler
    """ Values for changes in rotation

    :type: mathutils.Euler
    """

    scale: mathutils.Vector
    """ Values for changes in scale

    :type: mathutils.Vector
    """

    seed: int
    """ Random seed

    :type: int
    """

    stroke_start_offset: int
    """ Offset starting point

    :type: int
    """

    stroke_step: int
    """ Number of elements that will be grouped

    :type: int
    """

    use_uniform_random_scale: bool
    """ Use the same random seed for each scale axis for a uniform scale

    :type: bool
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
