import typing
import collections.abc
import mathutils
from .theme_space_gradient import ThemeSpaceGradient
from .struct import Struct
from .theme_asset_shelf import ThemeAssetShelf
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeView3D(bpy_struct):
    """Theme settings for the 3D viewport"""

    act_spline: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    asset_shelf: ThemeAssetShelf
    """ Settings for asset shelf

    :type: ThemeAssetShelf
    """

    bone_locked_weight: bpy_prop_array[float]
    """ Shade for bones corresponding to a locked weight group during painting

    :type: bpy_prop_array[float]
    """

    bone_pose: mathutils.Color
    """ Outline color of selected pose bones

    :type: mathutils.Color
    """

    bone_pose_active: mathutils.Color
    """ Outline color of active pose bones

    :type: mathutils.Color
    """

    bone_solid: mathutils.Color
    """ Default color of the solid shapes of bones

    :type: mathutils.Color
    """

    bundle_solid: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    camera: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    camera_passepartout: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    camera_path: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    clipping_border_3d: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    edge_bevel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    edge_crease: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    edge_facesel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    edge_mode_select: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    edge_seam: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    edge_select: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    edge_sharp: mathutils.Color
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

    empty: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    extra_edge_angle: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    extra_edge_len: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    extra_face_angle: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    extra_face_area: mathutils.Color
    """ 

    :type: mathutils.Color
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

    freestyle_edge_mark: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    freestyle_face_mark: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    gp_vertex: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    gp_vertex_select: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    gp_vertex_size: int
    """ 

    :type: int
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

    handle_sel_free: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_vect: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_vect: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    lastsel_point: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    light: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    normal: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    nurb_sel_uline: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    nurb_sel_vline: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    nurb_uline: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    nurb_vline: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    object_active: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    object_origin_size: int
    """ Diameter in pixels for object/light origin display

    :type: int
    """

    object_selected: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    outline_width: int
    """ 

    :type: int
    """

    paint_curve_handle: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    paint_curve_pivot: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    skin_root: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    space: ThemeSpaceGradient
    """ Settings for space

    :type: ThemeSpaceGradient
    """

    speaker: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    split_normal: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    text_grease_pencil: mathutils.Color
    """ Color for indicating Grease Pencil keyframes

    :type: mathutils.Color
    """

    text_keyframe: mathutils.Color
    """ Color for indicating object keyframes

    :type: mathutils.Color
    """

    transform: mathutils.Color
    """ 

    :type: mathutils.Color
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

    vertex_normal: mathutils.Color
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

    view_overlay: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    wire: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    wire_edit: mathutils.Color
    """ Color for wireframe when in edit mode, but edge selection is active

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
