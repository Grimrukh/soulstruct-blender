import typing
import collections.abc
import mathutils
from .curve_profile import CurveProfile
from .g_pencil_sculpt_settings import GPencilSculptSettings
from .sequencer_tool_settings import SequencerToolSettings
from .struct import Struct
from .sculpt import Sculpt
from .gp_sculpt_paint import GpSculptPaint
from .particle_edit import ParticleEdit
from .curves_sculpt import CurvesSculpt
from .paint_mode_settings import PaintModeSettings
from .gp_weight_paint import GpWeightPaint
from .vertex_paint import VertexPaint
from .curve_paint_settings import CurvePaintSettings
from .gp_paint import GpPaint
from .mesh_stat_vis import MeshStatVis
from .g_pencil_interpolate_settings import GPencilInterpolateSettings
from .gp_vertex_paint import GpVertexPaint
from .unified_paint_settings import UnifiedPaintSettings
from .bpy_struct import bpy_struct
from .uv_sculpt import UvSculpt
from .image_paint import ImagePaint

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ToolSettings(bpy_struct):
    annotation_stroke_placement_view2d: str
    """ 

    :type: str
    """

    annotation_stroke_placement_view3d: str
    """ How annotation strokes are orientated in 3D space

    :type: str
    """

    annotation_thickness: int
    """ Thickness of annotation strokes

    :type: int
    """

    auto_keying_mode: str
    """ Mode of automatic keyframe insertion for Objects, Bones and Masks

    :type: str
    """

    curve_paint_settings: CurvePaintSettings
    """ 

    :type: CurvePaintSettings
    """

    curves_sculpt: CurvesSculpt
    """ 

    :type: CurvesSculpt
    """

    custom_bevel_profile_preset: CurveProfile
    """ Used for defining a profile's path

    :type: CurveProfile
    """

    double_threshold: float
    """ Threshold distance for Auto Merge

    :type: float
    """

    gpencil_interpolate: GPencilInterpolateSettings
    """ Settings for Grease Pencil Interpolation tools

    :type: GPencilInterpolateSettings
    """

    gpencil_paint: GpPaint
    """ 

    :type: GpPaint
    """

    gpencil_sculpt: GPencilSculptSettings
    """ Settings for stroke sculpting tools and brushes

    :type: GPencilSculptSettings
    """

    gpencil_sculpt_paint: GpSculptPaint
    """ 

    :type: GpSculptPaint
    """

    gpencil_selectmode_edit: str
    """ 

    :type: str
    """

    gpencil_stroke_placement_view3d: str
    """ 

    :type: str
    """

    gpencil_stroke_snap_mode: str
    """ 

    :type: str
    """

    gpencil_surface_offset: float
    """ Offset along normal when drawing on surfaces

    :type: float
    """

    gpencil_vertex_paint: GpVertexPaint
    """ 

    :type: GpVertexPaint
    """

    gpencil_weight_paint: GpWeightPaint
    """ 

    :type: GpWeightPaint
    """

    image_paint: ImagePaint
    """ 

    :type: ImagePaint
    """

    keyframe_type: str
    """ Type of keyframes to create when inserting keyframes

    :type: str
    """

    lock_markers: bool
    """ Prevent marker editing

    :type: bool
    """

    lock_object_mode: bool
    """ Restrict selection to objects using the same mode as the active object, to prevent accidental mode switch when selecting

    :type: bool
    """

    mesh_select_mode: list[bool]
    """ Which mesh elements selection works on

    :type: list[bool]
    """

    normal_vector: mathutils.Vector
    """ Normal Vector used to copy, add or multiply

    :type: mathutils.Vector
    """

    paint_mode: PaintModeSettings
    """ 

    :type: PaintModeSettings
    """

    particle_edit: ParticleEdit
    """ 

    :type: ParticleEdit
    """

    plane_axis: str
    """ The axis used for placing the base region

    :type: str
    """

    plane_axis_auto: bool
    """ Select the closest axis when placing objects (surface overrides)

    :type: bool
    """

    plane_depth: str
    """ The initial depth used when placing the cursor

    :type: str
    """

    plane_orientation: str
    """ The initial depth used when placing the cursor

    :type: str
    """

    proportional_distance: float
    """ Display size for proportional editing circle

    :type: float
    """

    proportional_edit_falloff: str
    """ Falloff type for proportional editing mode

    :type: str
    """

    proportional_size: float
    """ Display size for proportional editing circle

    :type: float
    """

    sculpt: Sculpt
    """ 

    :type: Sculpt
    """

    sequencer_tool_settings: SequencerToolSettings
    """ 

    :type: SequencerToolSettings
    """

    show_uv_local_view: bool
    """ Display only faces with the currently displayed image assigned

    :type: bool
    """

    snap_anim_element: str
    """ Type of element to snap to

    :type: str
    """

    snap_elements: typing.Any
    """ Type of element to snap to"""

    snap_elements_base: set[str]
    """ Type of element for the 'Snap With' to snap to

    :type: set[str]
    """

    snap_elements_individual: set[str]
    """ Type of element for individual transformed elements to snap to

    :type: set[str]
    """

    snap_elements_tool: str
    """ The target to use while snapping

    :type: str
    """

    snap_face_nearest_steps: int
    """ Number of steps to break transformation into for face nearest snapping

    :type: int
    """

    snap_node_element: str
    """ Type of element to snap to

    :type: str
    """

    snap_target: str
    """ Which part to snap onto the target

    :type: str
    """

    snap_uv_element: str
    """ Type of element to snap to

    :type: str
    """

    statvis: MeshStatVis
    """ 

    :type: MeshStatVis
    """

    transform_pivot_point: str
    """ Pivot center for rotation/scaling

    :type: str
    """

    unified_paint_settings: UnifiedPaintSettings
    """ 

    :type: UnifiedPaintSettings
    """

    use_auto_normalize: bool
    """ Ensure all bone-deforming vertex groups add up to 1.0 while weight painting

    :type: bool
    """

    use_edge_path_live_unwrap: bool
    """ Changing edge seams recalculates UV unwrap

    :type: bool
    """

    use_gpencil_automerge_strokes: bool
    """ Join by distance last drawn stroke with previous strokes in the active layer

    :type: bool
    """

    use_gpencil_draw_additive: bool
    """ When creating new frames, the strokes from the previous/active frame are included as the basis for the new one

    :type: bool
    """

    use_gpencil_draw_onback: bool
    """ When draw new strokes, the new stroke is drawn below of all strokes in the layer

    :type: bool
    """

    use_gpencil_select_mask_point: bool
    """ Only sculpt selected stroke points

    :type: bool
    """

    use_gpencil_select_mask_segment: bool
    """ Only sculpt selected stroke points between other strokes

    :type: bool
    """

    use_gpencil_select_mask_stroke: bool
    """ Only sculpt selected stroke

    :type: bool
    """

    use_gpencil_stroke_endpoints: bool
    """ Only use the first and last parts of the stroke for snapping

    :type: bool
    """

    use_gpencil_thumbnail_list: bool
    """ Show compact list of color instead of thumbnails

    :type: bool
    """

    use_gpencil_vertex_select_mask_point: bool
    """ Only paint selected stroke points

    :type: bool
    """

    use_gpencil_vertex_select_mask_segment: bool
    """ Only paint selected stroke points between other strokes

    :type: bool
    """

    use_gpencil_vertex_select_mask_stroke: bool
    """ Only paint selected stroke

    :type: bool
    """

    use_gpencil_weight_data_add: bool
    """ When creating new strokes, the weight data is added according to the current vertex group and weight, if no vertex group selected, weight is not added

    :type: bool
    """

    use_keyframe_cycle_aware: bool
    """ For channels with cyclic extrapolation, keyframe insertion is automatically remapped inside the cycle time range, and keeps ends in sync. Curves newly added to actions with a Manual Frame Range and Cyclic Animation are automatically made cyclic

    :type: bool
    """

    use_keyframe_insert_auto: bool
    """ Automatic keyframe insertion for Objects, Bones and Masks

    :type: bool
    """

    use_keyframe_insert_keyingset: bool
    """ Automatic keyframe insertion using active Keying Set only

    :type: bool
    """

    use_lock_relative: bool
    """ Display bone-deforming groups as if all locked deform groups were deleted, and the remaining ones were re-normalized

    :type: bool
    """

    use_mesh_automerge: bool
    """ Automatically merge vertices moved to the same location

    :type: bool
    """

    use_mesh_automerge_and_split: bool
    """ Automatically split edges and faces

    :type: bool
    """

    use_multipaint: bool
    """ Paint across the weights of all selected bones, maintaining their relative influence

    :type: bool
    """

    use_proportional_action: bool
    """ Proportional editing in action editor

    :type: bool
    """

    use_proportional_connected: bool
    """ Proportional Editing using connected geometry only

    :type: bool
    """

    use_proportional_edit: bool
    """ Proportional edit mode

    :type: bool
    """

    use_proportional_edit_mask: bool
    """ Proportional editing mask mode

    :type: bool
    """

    use_proportional_edit_objects: bool
    """ Proportional editing object mode

    :type: bool
    """

    use_proportional_fcurve: bool
    """ Proportional editing in F-Curve editor

    :type: bool
    """

    use_proportional_projected: bool
    """ Proportional Editing using screen space locations

    :type: bool
    """

    use_record_with_nla: bool
    """ Add a new NLA Track + Strip for every loop/pass made over the animation to allow non-destructive tweaking

    :type: bool
    """

    use_snap: bool
    """ Snap during transform

    :type: bool
    """

    use_snap_align_rotation: bool
    """ Align rotation with the snapping target

    :type: bool
    """

    use_snap_anim: bool
    """ Enable snapping when transforming keyframes

    :type: bool
    """

    use_snap_backface_culling: bool
    """ Exclude back facing geometry from snapping

    :type: bool
    """

    use_snap_edit: bool
    """ Snap onto non-active objects in Edit Mode (Edit Mode Only)

    :type: bool
    """

    use_snap_grid_absolute: bool
    """ Absolute grid alignment while translating (based on the pivot center)

    :type: bool
    """

    use_snap_node: bool
    """ Snap Node during transform

    :type: bool
    """

    use_snap_nonedit: bool
    """ Snap onto objects not in Edit Mode (Edit Mode Only)

    :type: bool
    """

    use_snap_peel_object: bool
    """ Consider objects as whole when finding volume center

    :type: bool
    """

    use_snap_rotate: bool
    """ Rotate is affected by the snapping settings

    :type: bool
    """

    use_snap_scale: bool
    """ Scale is affected by snapping settings

    :type: bool
    """

    use_snap_selectable: bool
    """ Snap only onto objects that are selectable

    :type: bool
    """

    use_snap_self: bool
    """ Snap onto itself only if enabled (Edit Mode Only)

    :type: bool
    """

    use_snap_sequencer: bool
    """ Snap to strip edges or current frame

    :type: bool
    """

    use_snap_time_absolute: bool
    """ Absolute time alignment when transforming keyframes

    :type: bool
    """

    use_snap_to_same_target: bool
    """ Snap only to target that source was initially near (Face Nearest Only)

    :type: bool
    """

    use_snap_translate: bool
    """ Move is affected by snapping settings

    :type: bool
    """

    use_snap_uv: bool
    """ Snap UV during transform

    :type: bool
    """

    use_snap_uv_grid_absolute: bool
    """ Absolute grid alignment while translating (based on the pivot center)

    :type: bool
    """

    use_transform_correct_face_attributes: bool
    """ Correct data such as UVs and color attributes when transforming

    :type: bool
    """

    use_transform_correct_keep_connected: bool
    """ During the Face Attributes correction, merge attributes connected to the same vertex

    :type: bool
    """

    use_transform_data_origin: bool
    """ Transform object origins, while leaving the shape in place

    :type: bool
    """

    use_transform_pivot_point_align: bool
    """ Only transform object locations, without affecting rotation or scaling

    :type: bool
    """

    use_transform_skip_children: bool
    """ Transform the parents, leaving the children in place

    :type: bool
    """

    use_uv_select_sync: bool
    """ Keep UV and edit mode mesh selection in sync

    :type: bool
    """

    uv_relax_method: str
    """ Algorithm used for UV relaxation

    :type: str
    """

    uv_sculpt: UvSculpt
    """ 

    :type: UvSculpt
    """

    uv_sculpt_all_islands: bool
    """ Brush operates on all islands

    :type: bool
    """

    uv_sculpt_lock_borders: bool
    """ Disable editing of boundary edges

    :type: bool
    """

    uv_select_mode: str
    """ UV selection and display mode

    :type: str
    """

    uv_sticky_select_mode: str
    """ Method for extending UV vertex selection

    :type: str
    """

    vertex_group_subset: str
    """ Filter Vertex groups for Display

    :type: str
    """

    vertex_group_user: str
    """ Display unweighted vertices

    :type: str
    """

    vertex_group_weight: float
    """ Weight to assign in vertex groups

    :type: float
    """

    vertex_paint: VertexPaint
    """ 

    :type: VertexPaint
    """

    weight_paint: VertexPaint
    """ 

    :type: VertexPaint
    """

    workspace_tool_type: str
    """ Action when dragging in the viewport

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
