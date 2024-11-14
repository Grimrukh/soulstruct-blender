import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_profile import CurveProfile
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BevelModifier(Modifier, bpy_struct):
    """Bevel modifier to make edges and vertices more rounded"""

    affect: str
    """ Affect edges or vertices

    :type: str
    """

    angle_limit: float
    """ Angle above which to bevel edges

    :type: float
    """

    custom_profile: CurveProfile
    """ The path for the custom profile

    :type: CurveProfile
    """

    face_strength_mode: str
    """ Whether to set face strength, and which faces to set it on

    :type: str
    """

    harden_normals: bool
    """ Match normals of new faces to adjacent faces

    :type: bool
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    limit_method: str
    """ 

    :type: str
    """

    loop_slide: bool
    """ Prefer sliding along edges to having even widths

    :type: bool
    """

    mark_seam: bool
    """ Mark Seams along beveled edges

    :type: bool
    """

    mark_sharp: bool
    """ Mark beveled edges as sharp

    :type: bool
    """

    material: int
    """ Material index of generated faces, -1 for automatic

    :type: int
    """

    miter_inner: str
    """ Pattern to use for inside of miters

    :type: str
    """

    miter_outer: str
    """ Pattern to use for outside of miters

    :type: str
    """

    offset_type: str
    """ What distance Width measures

    :type: str
    """

    profile: float
    """ The profile shape (0.5 = round)

    :type: float
    """

    profile_type: str
    """ The type of shape used to rebuild a beveled section

    :type: str
    """

    segments: int
    """ Number of segments for round edges/verts

    :type: int
    """

    spread: float
    """ Spread distance for inner miter arcs

    :type: float
    """

    use_clamp_overlap: bool
    """ Clamp the width to avoid overlap

    :type: bool
    """

    vertex_group: str
    """ Vertex group name

    :type: str
    """

    vmesh_method: str
    """ The method to use to create the mesh at intersections

    :type: str
    """

    width: float
    """ Bevel amount

    :type: float
    """

    width_pct: float
    """ Bevel amount for percentage method

    :type: float
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
