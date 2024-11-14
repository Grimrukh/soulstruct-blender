import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CurvePaintSettings(bpy_struct):
    corner_angle: float
    """ Angles above this are considered corners

    :type: float
    """

    curve_type: str
    """ Type of curve to use for new strokes

    :type: str
    """

    depth_mode: str
    """ Method of projecting depth

    :type: str
    """

    error_threshold: int
    """ Allow deviation for a smoother, less precise line

    :type: int
    """

    fit_method: str
    """ Curve fitting method

    :type: str
    """

    radius_max: float
    """ Radius to use when the maximum pressure is applied (or when a tablet isn't used)

    :type: float
    """

    radius_min: float
    """ Minimum radius when the minimum pressure is applied (also the minimum when tapering)

    :type: float
    """

    radius_taper_end: float
    """ Taper factor for the radius of each point along the curve

    :type: float
    """

    radius_taper_start: float
    """ Taper factor for the radius of each point along the curve

    :type: float
    """

    surface_offset: float
    """ Offset the stroke from the surface

    :type: float
    """

    surface_plane: str
    """ Plane for projected stroke

    :type: str
    """

    use_corners_detect: bool
    """ Detect corners and use non-aligned handles

    :type: bool
    """

    use_offset_absolute: bool
    """ Apply a fixed offset (don't scale by the radius)

    :type: bool
    """

    use_pressure_radius: bool
    """ Map tablet pressure to curve radius

    :type: bool
    """

    use_stroke_endpoints: bool
    """ Use the start of the stroke for the depth

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
