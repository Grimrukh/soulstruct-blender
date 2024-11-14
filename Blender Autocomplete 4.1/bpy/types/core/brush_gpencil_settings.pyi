import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .curve_mapping import CurveMapping

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BrushGpencilSettings(bpy_struct):
    """Settings for grease pencil brush"""

    active_smooth_factor: float | None
    """ Amount of smoothing while drawing

    :type: float | None
    """

    angle: float
    """ Direction of the stroke at which brush gives maximal thickness (0° for horizontal)

    :type: float
    """

    angle_factor: float
    """ Reduce brush thickness by this factor when stroke is perpendicular to 'Angle' direction

    :type: float
    """

    aspect: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    brush_draw_mode: str
    """ Preselected mode when using this brush

    :type: str
    """

    caps_type: str
    """ The shape of the start and end of the stroke

    :type: str
    """

    curve_jitter: CurveMapping
    """ Curve used for the jitter effect

    :type: CurveMapping
    """

    curve_random_hue: CurveMapping
    """ Curve used for modulating effect

    :type: CurveMapping
    """

    curve_random_pressure: CurveMapping
    """ Curve used for modulating effect

    :type: CurveMapping
    """

    curve_random_saturation: CurveMapping
    """ Curve used for modulating effect

    :type: CurveMapping
    """

    curve_random_strength: CurveMapping
    """ Curve used for modulating effect

    :type: CurveMapping
    """

    curve_random_uv: CurveMapping
    """ Curve used for modulating effect

    :type: CurveMapping
    """

    curve_random_value: CurveMapping
    """ Curve used for modulating effect

    :type: CurveMapping
    """

    curve_sensitivity: CurveMapping
    """ Curve used for the sensitivity

    :type: CurveMapping
    """

    curve_strength: CurveMapping
    """ Curve used for the strength

    :type: CurveMapping
    """

    dilate: int
    """ Number of pixels to expand or contract fill area

    :type: int
    """

    eraser_mode: str
    """ Eraser Mode

    :type: str
    """

    eraser_strength_factor: float
    """ Amount of erasing for strength

    :type: float
    """

    eraser_thickness_factor: float
    """ Amount of erasing for thickness

    :type: float
    """

    extend_stroke_factor: float
    """ Strokes end extension for closing gaps, use zero to disable

    :type: float
    """

    fill_direction: str
    """ Direction of the fill

    :type: str
    """

    fill_draw_mode: str
    """ Mode to draw boundary limits

    :type: str
    """

    fill_extend_mode: str
    """ Types of stroke extensions used for closing gaps

    :type: str
    """

    fill_factor: float
    """ Factor for fill boundary accuracy, higher values are more accurate but slower

    :type: float
    """

    fill_layer_mode: str
    """ Layers used as boundaries

    :type: str
    """

    fill_simplify_level: int
    """ Number of simplify steps (large values reduce fill accuracy)

    :type: int
    """

    fill_threshold: float
    """ Threshold to consider color transparent for filling

    :type: float
    """

    gpencil_paint_icon: str
    """ 

    :type: str
    """

    gpencil_sculpt_icon: str
    """ 

    :type: str
    """

    gpencil_vertex_icon: str
    """ 

    :type: str
    """

    gpencil_weight_icon: str
    """ 

    :type: str
    """

    hardness: float
    """ Gradient from the center of Dot and Box strokes (set to 1 for a solid stroke)

    :type: float
    """

    input_samples: int
    """ Generate intermediate points for very fast mouse movements. Set to 0 to disable

    :type: int
    """

    material: Material
    """ Material used for strokes drawn using this brush

    :type: Material
    """

    material_alt: Material
    """ Material used for secondary uses for this brush

    :type: Material
    """

    outline_thickness_factor: float
    """ Thickness of the outline stroke relative to current brush thickness

    :type: float
    """

    pen_jitter: float
    """ Jitter factor for new strokes

    :type: float
    """

    pen_smooth_factor: float
    """ Amount of smoothing to apply after finish newly created strokes, to reduce jitter/noise

    :type: float
    """

    pen_smooth_steps: int
    """ Number of times to smooth newly created strokes

    :type: int
    """

    pen_strength: float
    """ Color strength for new strokes (affect alpha factor of color)

    :type: float
    """

    pen_subdivision_steps: int
    """ Number of times to subdivide newly created strokes, for less jagged strokes

    :type: int
    """

    pin_draw_mode: bool
    """ Pin the mode to the brush

    :type: bool
    """

    random_hue_factor: float
    """ Random factor to modify original hue

    :type: float
    """

    random_pressure: float
    """ Randomness factor for pressure in new strokes

    :type: float
    """

    random_saturation_factor: float
    """ Random factor to modify original saturation

    :type: float
    """

    random_strength: float
    """ Randomness factor strength in new strokes

    :type: float
    """

    random_value_factor: float
    """ Random factor to modify original value

    :type: float
    """

    show_fill: bool
    """ Show transparent lines to use as boundary for filling

    :type: bool
    """

    show_fill_boundary: bool
    """ Show help lines for filling to see boundaries

    :type: bool
    """

    show_fill_extend: bool
    """ Show help lines for stroke extension

    :type: bool
    """

    show_lasso: bool
    """ Do not display fill color while drawing the stroke

    :type: bool
    """

    simplify_factor: float
    """ Factor of Simplify using adaptive algorithm

    :type: float
    """

    use_active_layer_only: bool
    """ Only edit the active layer of the object

    :type: bool
    """

    use_collide_strokes: bool
    """ Check if extend lines collide with strokes

    :type: bool
    """

    use_default_eraser: bool
    """ Use this brush when enable eraser with fast switch key

    :type: bool
    """

    use_edit_position: bool
    """ The brush affects the position of the point

    :type: bool
    """

    use_edit_strength: bool
    """ The brush affects the color strength of the point

    :type: bool
    """

    use_edit_thickness: bool
    """ The brush affects the thickness of the point

    :type: bool
    """

    use_edit_uv: bool
    """ The brush affects the UV rotation of the point

    :type: bool
    """

    use_fill_limit: bool
    """ Fill only visible areas in viewport

    :type: bool
    """

    use_jitter_pressure: bool
    """ Use tablet pressure for jitter

    :type: bool
    """

    use_keep_caps_eraser: bool
    """ Keep the caps as they are and don't flatten them when erasing

    :type: bool
    """

    use_material_pin: bool
    """ Keep material assigned to brush

    :type: bool
    """

    use_occlude_eraser: bool
    """ Erase only strokes visible and not occluded

    :type: bool
    """

    use_pressure: bool
    """ Use tablet pressure

    :type: bool
    """

    use_random_press_hue: bool
    """ Use pressure to modulate randomness

    :type: bool
    """

    use_random_press_radius: bool
    """ Use pressure to modulate randomness

    :type: bool
    """

    use_random_press_sat: bool
    """ Use pressure to modulate randomness

    :type: bool
    """

    use_random_press_strength: bool
    """ Use pressure to modulate randomness

    :type: bool
    """

    use_random_press_uv: bool
    """ Use pressure to modulate randomness

    :type: bool
    """

    use_random_press_val: bool
    """ Use pressure to modulate randomness

    :type: bool
    """

    use_settings_outline: bool
    """ Convert stroke to perimeter

    :type: bool
    """

    use_settings_postprocess: bool
    """ Additional post processing options for new strokes

    :type: bool
    """

    use_settings_random: bool
    """ Random brush settings

    :type: bool
    """

    use_settings_stabilizer: bool
    """ Draw lines with a delay to allow smooth strokes. Press Shift key to override while drawing

    :type: bool
    """

    use_strength_pressure: bool
    """ Use tablet pressure for color strength

    :type: bool
    """

    use_stroke_random_hue: bool
    """ Use randomness at stroke level

    :type: bool
    """

    use_stroke_random_radius: bool
    """ Use randomness at stroke level

    :type: bool
    """

    use_stroke_random_sat: bool
    """ Use randomness at stroke level

    :type: bool
    """

    use_stroke_random_strength: bool
    """ Use randomness at stroke level

    :type: bool
    """

    use_stroke_random_uv: bool
    """ Use randomness at stroke level

    :type: bool
    """

    use_stroke_random_val: bool
    """ Use randomness at stroke level

    :type: bool
    """

    use_trim: bool
    """ Trim intersecting stroke ends

    :type: bool
    """

    uv_random: float
    """ Random factor for auto-generated UV rotation

    :type: float
    """

    vertex_color_factor: float
    """ Factor used to mix vertex color to get final color

    :type: float
    """

    vertex_mode: str
    """ Defines how vertex color affect to the strokes

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
