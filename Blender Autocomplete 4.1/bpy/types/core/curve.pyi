import typing
import collections.abc
import mathutils
from .key import Key
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_profile import CurveProfile
from .anim_data import AnimData
from .id import ID
from .object import Object
from .id_materials import IDMaterials
from .curve_splines import CurveSplines

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Curve(ID, bpy_struct):
    """Curve data-block storing curves, splines and NURBS"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    bevel_depth: float
    """ Radius of the bevel geometry, not including extrusion

    :type: float
    """

    bevel_factor_end: float
    """ Define where along the spline the curve geometry ends (0 for the beginning, 1 for the end)

    :type: float
    """

    bevel_factor_mapping_end: str
    """ Determine how the geometry end factor is mapped to a spline

    :type: str
    """

    bevel_factor_mapping_start: str
    """ Determine how the geometry start factor is mapped to a spline

    :type: str
    """

    bevel_factor_start: float
    """ Define where along the spline the curve geometry starts (0 for the beginning, 1 for the end)

    :type: float
    """

    bevel_mode: str
    """ Determine how to build the curve's bevel geometry

    :type: str
    """

    bevel_object: Object
    """ The name of the Curve object that defines the bevel shape

    :type: Object
    """

    bevel_profile: CurveProfile
    """ The path for the curve's custom profile

    :type: CurveProfile
    """

    bevel_resolution: int
    """ The number of segments in each quarter-circle of the bevel

    :type: int
    """

    cycles: typing.Any
    """ Cycles mesh settings

    :type: typing.Any
    """

    dimensions: str
    """ Select 2D or 3D curve type

    :type: str
    """

    eval_time: float
    """ Parametric position along the length of the curve that Objects 'following' it should be at (position is evaluated by dividing by the 'Path Length' value)

    :type: float
    """

    extrude: float
    """ Length of the depth added in the local Z direction along the curve, perpendicular to its normals

    :type: float
    """

    fill_mode: str
    """ Mode of filling curve

    :type: str
    """

    is_editmode: bool
    """ True when used in editmode

    :type: bool
    """

    materials: IDMaterials
    """ 

    :type: IDMaterials
    """

    offset: float
    """ Distance to move the curve parallel to its normals

    :type: float
    """

    path_duration: int
    """ The number of frames that are needed to traverse the path, defining the maximum value for the 'Evaluation Time' setting

    :type: int
    """

    render_resolution_u: int
    """ Surface resolution in U direction used while rendering (zero uses preview resolution)

    :type: int
    """

    render_resolution_v: int
    """ Surface resolution in V direction used while rendering (zero uses preview resolution)

    :type: int
    """

    resolution_u: int
    """ Number of computed points in the U direction between every pair of control points

    :type: int
    """

    resolution_v: int
    """ The number of computed points in the V direction between every pair of control points

    :type: int
    """

    shape_keys: Key
    """ 

    :type: Key
    """

    splines: CurveSplines
    """ Collection of splines in this curve data object

    :type: CurveSplines
    """

    taper_object: Object
    """ Curve object name that defines the taper (width)

    :type: Object
    """

    taper_radius_mode: str
    """ Determine how the effective radius of the spline point is computed when a taper object is specified

    :type: str
    """

    texspace_location: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    texspace_size: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    twist_mode: str
    """ The type of tilt calculation for 3D Curves

    :type: str
    """

    twist_smooth: float
    """ Smoothing iteration for tangents

    :type: float
    """

    use_auto_texspace: bool
    """ Adjust active object's texture space automatically when transforming object

    :type: bool
    """

    use_deform_bounds: bool
    """ Option for curve-deform: Use the mesh bounds to clamp the deformation

    :type: bool
    """

    use_fill_caps: bool
    """ Fill caps for beveled curves

    :type: bool
    """

    use_map_taper: bool
    """ Map effect of the taper object to the beveled part of the curve

    :type: bool
    """

    use_path: bool
    """ Enable the curve to become a translation path

    :type: bool
    """

    use_path_clamp: bool
    """ Clamp the curve path children so they can't travel past the start/end point of the curve

    :type: bool
    """

    use_path_follow: bool
    """ Make curve path children rotate along the path

    :type: bool
    """

    use_radius: bool
    """ Option for paths and curve-deform: apply the curve radius to objects following it and to deformed objects

    :type: bool
    """

    use_stretch: bool
    """ Option for curve-deform: make deformed child stretch along entire path

    :type: bool
    """

    def transform(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        shape_keys: bool | typing.Any | None = False,
    ):
        """Transform curve by a matrix

        :param matrix: Matrix
        :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
        :param shape_keys: Transform Shape Keys
        :type shape_keys: bool | typing.Any | None
        """
        ...

    def validate_material_indices(self) -> bool:
        """Validate material indices of splines or letters, return True when the curve has had invalid indices corrected (to default 0)

        :return: Result
        :rtype: bool
        """
        ...

    def update_gpu_tag(self):
        """update_gpu_tag"""
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
