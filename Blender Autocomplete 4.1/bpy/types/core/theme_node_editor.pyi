import typing
import collections.abc
import mathutils
from .struct import Struct
from .theme_space_list_generic import ThemeSpaceListGeneric
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .theme_space_generic import ThemeSpaceGeneric

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeNodeEditor(bpy_struct):
    """Theme settings for the Node Editor"""

    attribute_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    color_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    converter_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    dash_alpha: float
    """ Opacity for the dashed lines in wires

    :type: float
    """

    distor_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    filter_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    frame_node: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    geometry_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    grid: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    grid_levels: int
    """ Number of subdivisions for the dot grid displayed in the background

    :type: int
    """

    group_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    group_socket_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    input_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    layout_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    matte_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    node_active: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    node_backdrop: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    node_selected: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    noodle_curving: int
    """ Curving of the noodle

    :type: int
    """

    output_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    pattern_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    repeat_zone: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    script_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    selected_text: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    shader_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    simulation_zone: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    space: ThemeSpaceGeneric
    """ Settings for space

    :type: ThemeSpaceGeneric
    """

    space_list: ThemeSpaceListGeneric
    """ Settings for space list

    :type: ThemeSpaceListGeneric
    """

    texture_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vector_node: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    wire: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    wire_inner: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    wire_select: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
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
