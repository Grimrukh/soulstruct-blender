import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .theme_space_generic import ThemeSpaceGeneric

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeImageEditor(bpy_struct):
    """Theme settings for the Image Editor"""

    edge_select: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    edge_width: int
    """ 

    :type: int
    """

    editmesh_active: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    face: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    face_back: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    face_dot: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    face_front: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    face_mode_select: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    face_retopology: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    face_select: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    facedot_size: int
    """ 

    :type: int
    """

    frame_current: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    freestyle_face_mark: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    grid: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    handle_align: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_auto: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_auto_clamped: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_free: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_align: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_auto: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_auto_clamped: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_free: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_vertex: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_vertex_select: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_vertex_size: int
    """ 

    :type: int
    """

    metadatabg: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    metadatatext: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    paint_curve_handle: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    paint_curve_pivot: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    preview_stitch_active: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    preview_stitch_edge: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    preview_stitch_face: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    preview_stitch_stitchable: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    preview_stitch_unstitchable: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    preview_stitch_vert: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    scope_back: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    space: ThemeSpaceGeneric
    """ Settings for space

    :type: ThemeSpaceGeneric
    """

    uv_shadow: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    vertex: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vertex_active: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vertex_bevel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vertex_select: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vertex_size: int
    """ 

    :type: int
    """

    vertex_unreferenced: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    wire_edit: mathutils.Color
    """ 

    :type: mathutils.Color
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
