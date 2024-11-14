import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GreasePencilOffsetModifier(Modifier, bpy_struct):
    invert_layer_filter: bool
    """ Invert layer filter

    :type: bool
    """

    invert_layer_pass_filter: bool
    """ Invert layer pass filter

    :type: bool
    """

    invert_material_filter: bool
    """ Invert material filter

    :type: bool
    """

    invert_material_pass_filter: bool
    """ Invert material pass filter

    :type: bool
    """

    invert_vertex_group: bool
    """ Invert vertex group weights

    :type: bool
    """

    layer_filter: str
    """ Layer name

    :type: str
    """

    layer_pass_filter: int
    """ Layer pass filter

    :type: int
    """

    location: mathutils.Vector
    """ Values for change location

    :type: mathutils.Vector
    """

    material_filter: Material
    """ Material used for filtering

    :type: Material
    """

    material_pass_filter: int
    """ Material pass

    :type: int
    """

    offset_mode: str
    """ 

    :type: str
    """

    open_influence_panel: bool
    """ 

    :type: bool
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

    stroke_location: mathutils.Vector
    """ Value for changes in location

    :type: mathutils.Vector
    """

    stroke_rotation: mathutils.Euler
    """ Value for changes in rotation

    :type: mathutils.Euler
    """

    stroke_scale: mathutils.Vector
    """ Value for changes in scale

    :type: mathutils.Vector
    """

    stroke_start_offset: int
    """ Offset starting point

    :type: int
    """

    stroke_step: int
    """ Number of elements that will be grouped

    :type: int
    """

    use_layer_pass_filter: bool
    """ Use layer pass filter

    :type: bool
    """

    use_material_pass_filter: bool
    """ Use material pass filter

    :type: bool
    """

    use_uniform_random_scale: bool
    """ Use the same random seed for each scale axis for a uniform scale

    :type: bool
    """

    vertex_group_name: str
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
