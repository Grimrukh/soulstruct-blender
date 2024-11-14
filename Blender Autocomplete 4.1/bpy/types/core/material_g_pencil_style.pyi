import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .image import Image

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaterialGPencilStyle(bpy_struct):
    alignment_mode: str
    """ Defines how align Dots and Boxes with drawing path and object rotation

    :type: str
    """

    alignment_rotation: float
    """ Additional rotation applied to dots and square texture of strokes. Only applies in texture shading mode

    :type: float
    """

    color: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    fill_color: bpy_prop_array[float]
    """ Color for filling region bounded by each stroke

    :type: bpy_prop_array[float]
    """

    fill_image: Image
    """ 

    :type: Image
    """

    fill_style: str
    """ Select style used to fill strokes

    :type: str
    """

    flip: bool
    """ Flip filling colors

    :type: bool
    """

    ghost: bool
    """ Display strokes using this color when showing onion skins

    :type: bool
    """

    gradient_type: str
    """ Select type of gradient used to fill strokes

    :type: str
    """

    hide: bool
    """ Set color Visibility

    :type: bool
    """

    is_fill_visible: bool
    """ True when opacity of fill is set high enough to be visible

    :type: bool
    """

    is_stroke_visible: bool
    """ True when opacity of stroke is set high enough to be visible

    :type: bool
    """

    lock: bool
    """ Protect color from further editing and/or frame changes

    :type: bool
    """

    mix_color: bpy_prop_array[float]
    """ Color for mixing with primary filling color

    :type: bpy_prop_array[float]
    """

    mix_factor: float
    """ Mix Factor

    :type: float
    """

    mix_stroke_factor: float
    """ Mix Stroke Factor

    :type: float
    """

    mode: str
    """ Select line type for strokes

    :type: str
    """

    pass_index: int
    """ Index number for the "Color Index" pass

    :type: int
    """

    pixel_size: float
    """ Texture Pixel Size factor along the stroke

    :type: float
    """

    show_fill: bool
    """ Show stroke fills of this material

    :type: bool
    """

    show_stroke: bool
    """ Show stroke lines of this material

    :type: bool
    """

    stroke_image: Image
    """ 

    :type: Image
    """

    stroke_style: str
    """ Select style used to draw strokes

    :type: str
    """

    texture_angle: float
    """ Texture Orientation Angle

    :type: float
    """

    texture_clamp: bool
    """ Do not repeat texture and clamp to one instance only

    :type: bool
    """

    texture_offset: mathutils.Vector
    """ Shift Texture in 2d Space

    :type: mathutils.Vector
    """

    texture_scale: mathutils.Vector
    """ Scale Factor for Texture

    :type: mathutils.Vector
    """

    use_fill_holdout: bool
    """ Remove the color from underneath this stroke by using it as a mask

    :type: bool
    """

    use_overlap_strokes: bool
    """ Disable stencil and overlap self intersections with alpha materials

    :type: bool
    """

    use_stroke_holdout: bool
    """ Remove the color from underneath this stroke by using it as a mask

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
