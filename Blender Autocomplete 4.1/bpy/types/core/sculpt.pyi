import typing
import collections.abc
import mathutils
from .struct import Struct
from .paint import Paint
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .curve_mapping import CurveMapping
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Sculpt(Paint, bpy_struct):
    automasking_boundary_edges_propagation_steps: int
    """ Distance where boundary edge automasking is going to protect vertices from the fully masked edge

    :type: int
    """

    automasking_cavity_blur_steps: int
    """ The number of times the cavity mask is blurred

    :type: int
    """

    automasking_cavity_curve: CurveMapping
    """ Curve used for the sensitivity

    :type: CurveMapping
    """

    automasking_cavity_curve_op: CurveMapping
    """ Curve used for the sensitivity

    :type: CurveMapping
    """

    automasking_cavity_factor: float
    """ The contrast of the cavity mask

    :type: float
    """

    automasking_start_normal_falloff: float
    """ Extend the angular range with a falloff gradient

    :type: float
    """

    automasking_start_normal_limit: float
    """ The range of angles that will be affected

    :type: float
    """

    automasking_view_normal_falloff: float
    """ Extend the angular range with a falloff gradient

    :type: float
    """

    automasking_view_normal_limit: float
    """ The range of angles that will be affected

    :type: float
    """

    constant_detail_resolution: float
    """ Maximum edge length for dynamic topology sculpting (as divisor of Blender unit - higher value means smaller edge length)

    :type: float
    """

    detail_percent: float
    """ Maximum edge length for dynamic topology sculpting (in brush percenage)

    :type: float
    """

    detail_refine_method: str
    """ In dynamic-topology mode, how to add or remove mesh detail

    :type: str
    """

    detail_size: float
    """ Maximum edge length for dynamic topology sculpting (in pixels)

    :type: float
    """

    detail_type_method: str
    """ In dynamic-topology mode, how mesh detail size is calculated

    :type: str
    """

    gravity: float
    """ Amount of gravity after each dab

    :type: float
    """

    gravity_object: Object
    """ Object whose Z axis defines orientation of gravity

    :type: Object
    """

    lock_x: bool
    """ Disallow changes to the X axis of vertices

    :type: bool
    """

    lock_y: bool
    """ Disallow changes to the Y axis of vertices

    :type: bool
    """

    lock_z: bool
    """ Disallow changes to the Z axis of vertices

    :type: bool
    """

    radial_symmetry: bpy_prop_array[int]
    """ Number of times to copy strokes across the surface

    :type: bpy_prop_array[int]
    """

    symmetrize_direction: str
    """ Source and destination for symmetrize operator

    :type: str
    """

    transform_mode: str
    """ How the transformation is going to be applied to the target

    :type: str
    """

    use_automasking_boundary_edges: bool
    """ Do not affect non manifold boundary edges

    :type: bool
    """

    use_automasking_boundary_face_sets: bool
    """ Do not affect vertices that belong to a Face Set boundary

    :type: bool
    """

    use_automasking_cavity: bool
    """ Do not affect vertices on peaks, based on the surface curvature

    :type: bool
    """

    use_automasking_cavity_inverted: bool
    """ Do not affect vertices within crevices, based on the surface curvature

    :type: bool
    """

    use_automasking_custom_cavity_curve: bool
    """ Use custom curve

    :type: bool
    """

    use_automasking_face_sets: bool
    """ Affect only vertices that share Face Sets with the active vertex

    :type: bool
    """

    use_automasking_start_normal: bool
    """ Affect only vertices with a similar normal to where the stroke starts

    :type: bool
    """

    use_automasking_topology: bool
    """ Affect only vertices connected to the active vertex under the brush

    :type: bool
    """

    use_automasking_view_normal: bool
    """ Affect only vertices with a normal that faces the viewer

    :type: bool
    """

    use_automasking_view_occlusion: bool
    """ Only affect vertices that are not occluded by other faces. (Slower performance)

    :type: bool
    """

    use_deform_only: bool
    """ Use only deformation modifiers (temporary disable all constructive modifiers except multi-resolution)

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
