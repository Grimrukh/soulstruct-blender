import typing
import collections.abc
import mathutils
from .g_pencil_stroke_points import GPencilStrokePoints
from .bpy_prop_collection import bpy_prop_collection
from .g_pencil_triangle import GPencilTriangle
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .g_pencil_edit_curve import GPencilEditCurve

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilStroke(bpy_struct):
    """Freehand curve defining part of a sketch"""

    aspect: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    bound_box_max: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    bound_box_min: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    display_mode: str
    """ Coordinate space that stroke is in

    :type: str
    """

    edit_curve: GPencilEditCurve
    """ Temporary data for Edit Curve

    :type: GPencilEditCurve
    """

    end_cap_mode: str
    """ Stroke end extreme cap style

    :type: str
    """

    hardness: float
    """ Amount of gradient along section of stroke

    :type: float
    """

    has_edit_curve: bool
    """ Stroke has Curve data to edit shape

    :type: bool
    """

    is_nofill_stroke: bool
    """ Special stroke to use as boundary for filling areas

    :type: bool
    """

    line_width: int
    """ Thickness of stroke (in pixels)

    :type: int
    """

    material_index: int
    """ Material slot index of this stroke

    :type: int
    """

    points: GPencilStrokePoints
    """ Stroke data points

    :type: GPencilStrokePoints
    """

    select: bool
    """ Stroke is selected for viewport editing

    :type: bool
    """

    select_index: int
    """ Index of selection used for interpolation

    :type: int
    """

    start_cap_mode: str
    """ Stroke start extreme cap style

    :type: str
    """

    time_start: float
    """ Initial time of the stroke

    :type: float
    """

    triangles: bpy_prop_collection[GPencilTriangle]
    """ Triangulation data for HQ fill

    :type: bpy_prop_collection[GPencilTriangle]
    """

    use_cyclic: bool
    """ Enable cyclic drawing, closing the stroke

    :type: bool
    """

    uv_rotation: float
    """ Rotation of the UV

    :type: float
    """

    uv_scale: float
    """ Scale of the UV

    :type: float
    """

    uv_translation: mathutils.Vector
    """ Translation of default UV position

    :type: mathutils.Vector
    """

    vertex_color_fill: bpy_prop_array[float]
    """ Color used to mix with fill color to get final color

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
