import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .spline_bezier_points import SplineBezierPoints
from .spline_points import SplinePoints

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Spline(bpy_struct):
    """Element of a curve, either NURBS, Bézier or Polyline or a character with text objects"""

    bezier_points: SplineBezierPoints
    """ Collection of points for Bézier curves only

    :type: SplineBezierPoints
    """

    character_index: int
    """ Location of this character in the text data (only for text curves)

    :type: int
    """

    hide: bool
    """ Hide this curve in Edit mode

    :type: bool
    """

    material_index: int
    """ Material slot index of this curve

    :type: int
    """

    order_u: int
    """ NURBS order in the U direction. Higher values make each point influence a greater area, but have worse performance

    :type: int
    """

    order_v: int
    """ NURBS order in the V direction. Higher values make each point influence a greater area, but have worse performance

    :type: int
    """

    point_count_u: int
    """ Total number points for the curve or surface in the U direction

    :type: int
    """

    point_count_v: int
    """ Total number points for the surface on the V direction

    :type: int
    """

    points: SplinePoints
    """ Collection of points that make up this poly or nurbs spline

    :type: SplinePoints
    """

    radius_interpolation: str
    """ The type of radius interpolation for Bézier curves

    :type: str
    """

    resolution_u: int
    """ Curve or Surface subdivisions per segment

    :type: int
    """

    resolution_v: int
    """ Surface subdivisions per segment

    :type: int
    """

    tilt_interpolation: str
    """ The type of tilt interpolation for 3D, Bézier curves

    :type: str
    """

    type: str
    """ The interpolation type for this curve element

    :type: str
    """

    use_bezier_u: bool
    """ Make this nurbs curve or surface act like a Bézier spline in the U direction

    :type: bool
    """

    use_bezier_v: bool
    """ Make this nurbs surface act like a Bézier spline in the V direction

    :type: bool
    """

    use_cyclic_u: bool
    """ Make this curve or surface a closed loop in the U direction

    :type: bool
    """

    use_cyclic_v: bool
    """ Make this surface a closed loop in the V direction

    :type: bool
    """

    use_endpoint_u: bool
    """ Make this nurbs curve or surface meet the endpoints in the U direction

    :type: bool
    """

    use_endpoint_v: bool
    """ Make this nurbs surface meet the endpoints in the V direction

    :type: bool
    """

    use_smooth: bool
    """ Smooth the normals of the surface or beveled curve

    :type: bool
    """

    def calc_length(self, resolution: typing.Any | None = 0) -> float:
        """Calculate spline length

        :param resolution: Resolution, Spline resolution to be used, 0 defaults to the resolution_u
        :type resolution: typing.Any | None
        :return: Length, Length of the polygonaly approximated spline
        :rtype: float
        """
        ...

    def valid_message(self, direction: int | None) -> str:
        """Return the message

        :param direction: Direction, The direction where 0-1 maps to U-V
        :type direction: int | None
        :return: Return value, The message or an empty string when there is no error
        :rtype: str
        """
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
