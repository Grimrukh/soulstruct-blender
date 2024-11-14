import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PreferencesEdit(bpy_struct):
    """Settings for interacting with Blender data"""

    auto_keying_mode: str
    """ Mode of automatic keyframe insertion for Objects and Bones (default setting used for new Scenes)

    :type: str
    """

    collection_instance_empty_size: float
    """ Display size of the empty when new collection instances are created

    :type: float
    """

    fcurve_new_auto_smoothing: str
    """ Auto Handle Smoothing mode used for newly added F-Curves

    :type: str
    """

    fcurve_unselected_alpha: float
    """ The opacity of unselected F-Curves against the background of the Graph Editor

    :type: float
    """

    grease_pencil_default_color: bpy_prop_array[float]
    """ Color of new annotation layers

    :type: bpy_prop_array[float]
    """

    grease_pencil_eraser_radius: int
    """ Radius of eraser 'brush'

    :type: int
    """

    grease_pencil_euclidean_distance: int
    """ Distance moved by mouse when drawing stroke to include

    :type: int
    """

    grease_pencil_manhattan_distance: int
    """ Pixels moved by mouse per axis when drawing stroke

    :type: int
    """

    key_insert_channels: set[str]
    """ Which channels to insert keys at when no keying set is active

    :type: set[str]
    """

    keyframe_new_handle_type: str
    """ Handle type for handles of new keyframes

    :type: str
    """

    keyframe_new_interpolation_type: str
    """ Interpolation mode used for first keyframe on newly added F-Curves (subsequent keyframes take interpolation from preceding keyframe)

    :type: str
    """

    material_link: str
    """ Toggle whether the material is linked to object data or the object block

    :type: str
    """

    node_margin: int
    """ Minimum distance between nodes for Auto-offsetting nodes

    :type: int
    """

    node_preview_resolution: int
    """ Resolution used for Shader node previews (should be changed for performance convenience)

    :type: int
    """

    node_use_insert_offset: bool
    """ Automatically offset the following or previous nodes in a chain when inserting a new node

    :type: bool
    """

    object_align: str
    """ The default alignment for objects added from a 3D viewport menu

    :type: str
    """

    sculpt_paint_overlay_color: mathutils.Color
    """ Color of texture overlay

    :type: mathutils.Color
    """

    show_only_selected_curve_keyframes: bool
    """ Only keyframes of selected F-Curves are visible and editable

    :type: bool
    """

    undo_memory_limit: int
    """ Maximum memory usage in megabytes (0 means unlimited)

    :type: int
    """

    undo_steps: int
    """ Number of undo steps available (smaller values conserve memory)

    :type: int
    """

    use_anim_channel_group_colors: bool
    """ Use animation channel group colors; generally this is used to show bone group colors

    :type: bool
    """

    use_auto_keyframe_insert_needed: bool
    """ Auto-Keying will skip inserting keys that don't affect the animation

    :type: bool
    """

    use_auto_keying: bool
    """ Automatic keyframe insertion for Objects and Bones (default setting used for new Scenes)

    :type: bool
    """

    use_auto_keying_warning: bool
    """ Show warning indicators when transforming objects and bones if auto keying is enabled

    :type: bool
    """

    use_cursor_lock_adjust: bool
    """ Place the cursor without 'jumping' to the new location (when lock-to-cursor is used)

    :type: bool
    """

    use_duplicate_action: bool
    """ Causes actions to be duplicated with the data-blocks

    :type: bool
    """

    use_duplicate_armature: bool
    """ Causes armature data to be duplicated with the object

    :type: bool
    """

    use_duplicate_camera: bool
    """ Causes camera data to be duplicated with the object

    :type: bool
    """

    use_duplicate_curve: bool
    """ Causes curve data to be duplicated with the object

    :type: bool
    """

    use_duplicate_curves: bool
    """ Causes curves data to be duplicated with the object

    :type: bool
    """

    use_duplicate_grease_pencil: bool
    """ Causes grease pencil data to be duplicated with the object

    :type: bool
    """

    use_duplicate_lattice: bool
    """ Causes lattice data to be duplicated with the object

    :type: bool
    """

    use_duplicate_light: bool
    """ Causes light data to be duplicated with the object

    :type: bool
    """

    use_duplicate_lightprobe: bool
    """ Causes light probe data to be duplicated with the object

    :type: bool
    """

    use_duplicate_material: bool
    """ Causes material data to be duplicated with the object

    :type: bool
    """

    use_duplicate_mesh: bool
    """ Causes mesh data to be duplicated with the object

    :type: bool
    """

    use_duplicate_metaball: bool
    """ Causes metaball data to be duplicated with the object

    :type: bool
    """

    use_duplicate_node_tree: bool
    """ Make copies of node groups when duplicating nodes in the node editor

    :type: bool
    """

    use_duplicate_particle: bool
    """ Causes particle systems to be duplicated with the object

    :type: bool
    """

    use_duplicate_pointcloud: bool
    """ Causes point cloud data to be duplicated with the object

    :type: bool
    """

    use_duplicate_speaker: bool
    """ Causes speaker data to be duplicated with the object

    :type: bool
    """

    use_duplicate_surface: bool
    """ Causes surface data to be duplicated with the object

    :type: bool
    """

    use_duplicate_text: bool
    """ Causes text data to be duplicated with the object

    :type: bool
    """

    use_duplicate_volume: bool
    """ Causes volume data to be duplicated with the object

    :type: bool
    """

    use_enter_edit_mode: bool
    """ Enter edit mode automatically after adding a new object

    :type: bool
    """

    use_fcurve_high_quality_drawing: bool
    """ Draw F-Curves using Anti-Aliasing (disable for better performance)

    :type: bool
    """

    use_global_undo: bool
    """ Global undo works by keeping a full copy of the file itself in memory, so takes extra memory

    :type: bool
    """

    use_insertkey_xyz_to_rgb: bool
    """ Color for newly added transformation F-Curves (Location, Rotation, Scale) and also Color is based on the transform axis

    :type: bool
    """

    use_keyframe_insert_available: bool
    """ Insert Keyframes only for properties that are already animated

    :type: bool
    """

    use_keyframe_insert_needed: bool
    """ When keying manually, skip inserting keys that don't affect the animation

    :type: bool
    """

    use_mouse_depth_cursor: bool
    """ Use the surface depth for cursor placement

    :type: bool
    """

    use_negative_frames: bool
    """ Current frame number can be manually set to a negative value

    :type: bool
    """

    use_text_edit_auto_close: bool
    """ Automatically close relevant character pairs when typing in the text editor

    :type: bool
    """

    use_visual_keying: bool
    """ Use Visual keying automatically for constrained objects

    :type: bool
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
