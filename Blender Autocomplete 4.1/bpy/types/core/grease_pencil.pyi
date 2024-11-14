import typing
import collections.abc
import mathutils
from .grease_pencil_grid import GreasePencilGrid
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .anim_data import AnimData
from .id import ID
from .grease_pencil_layers import GreasePencilLayers
from .id_materials import IDMaterials

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GreasePencil(ID, bpy_struct):
    """Freehand annotation sketchbook"""

    after_color: mathutils.Color
    """ Base color for ghosts after the active frame

    :type: mathutils.Color
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    before_color: mathutils.Color
    """ Base color for ghosts before the active frame

    :type: mathutils.Color
    """

    curve_edit_corner_angle: float
    """ Angles above this are considered corners

    :type: float
    """

    curve_edit_threshold: float
    """ Curve conversion error threshold

    :type: float
    """

    edit_curve_resolution: int
    """ Number of segments generated between control points when editing strokes in curve mode

    :type: int
    """

    edit_line_color: bpy_prop_array[float]
    """ Color for editing line

    :type: bpy_prop_array[float]
    """

    ghost_after_range: int
    """ Maximum number of frames to show after current frame (0 = don't show any frames after current)

    :type: int
    """

    ghost_before_range: int
    """ Maximum number of frames to show before current frame (0 = don't show any frames before current)

    :type: int
    """

    grid: GreasePencilGrid
    """ Settings for grid and canvas in the 3D viewport

    :type: GreasePencilGrid
    """

    is_annotation: bool
    """ Current data-block is an annotation

    :type: bool
    """

    is_stroke_paint_mode: bool
    """ Draw Grease Pencil strokes on click/drag

    :type: bool
    """

    is_stroke_sculpt_mode: bool
    """ Sculpt Grease Pencil strokes instead of viewport data

    :type: bool
    """

    is_stroke_vertex_mode: bool
    """ Grease Pencil vertex paint

    :type: bool
    """

    is_stroke_weight_mode: bool
    """ Grease Pencil weight paint

    :type: bool
    """

    layers: GreasePencilLayers
    """ 

    :type: GreasePencilLayers
    """

    materials: IDMaterials
    """ 

    :type: IDMaterials
    """

    onion_factor: float
    """ Change fade opacity of displayed onion frames

    :type: float
    """

    onion_keyframe_type: str
    """ Type of keyframe (for filtering)

    :type: str
    """

    onion_mode: str
    """ Mode to display frames

    :type: str
    """

    pixel_factor: float
    """ Scale conversion factor for pixel size (use larger values for thicker lines)

    :type: float
    """

    stroke_depth_order: str
    """ Defines how the strokes are ordered in 3D space (for objects not displayed 'In Front')

    :type: str
    """

    stroke_thickness_space: str
    """ Set stroke thickness in screen space or world space

    :type: str
    """

    use_adaptive_curve_resolution: bool
    """ Set the resolution of each editcurve segment dynamically depending on the length of the segment. The resolution is the number of points generated per unit distance

    :type: bool
    """

    use_autolock_layers: bool
    """ Automatically lock all layers except the active one to avoid accidental changes

    :type: bool
    """

    use_curve_edit: bool
    """ Edit strokes using curve handles

    :type: bool
    """

    use_ghost_custom_colors: bool
    """ Use custom colors for ghost frames

    :type: bool
    """

    use_ghosts_always: bool
    """ Ghosts are shown in renders and animation playback. Useful for special effects (e.g. motion blur)

    :type: bool
    """

    use_multiedit: bool
    """ Edit strokes from multiple grease pencil keyframes at the same time (keyframes must be selected to be included)

    :type: bool
    """

    use_onion_fade: bool
    """ Display onion keyframes with a fade in color transparency

    :type: bool
    """

    use_onion_loop: bool
    """ Display onion keyframes for looping animations

    :type: bool
    """

    use_onion_skinning: bool
    """ Show ghosts of the keyframes before and after the current frame

    :type: bool
    """

    use_stroke_edit_mode: bool
    """ Edit Grease Pencil strokes instead of viewport data

    :type: bool
    """

    zdepth_offset: float
    """ Offset amount when drawing in surface mode

    :type: float
    """

    def clear(self):
        """Remove all the Grease Pencil data"""
        ...

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
