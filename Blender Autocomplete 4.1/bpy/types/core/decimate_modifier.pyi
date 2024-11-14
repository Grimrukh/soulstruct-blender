import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DecimateModifier(Modifier, bpy_struct):
    """Decimation modifier"""

    angle_limit: float
    """ Only dissolve angles below this (planar only)

    :type: float
    """

    decimate_type: str
    """ 

    :type: str
    """

    delimit: typing.Any
    """ Limit merging geometry"""

    face_count: int
    """ The current number of faces in the decimated mesh

    :type: int
    """

    invert_vertex_group: bool
    """ Invert vertex group influence (collapse only)

    :type: bool
    """

    iterations: int
    """ Number of times reduce the geometry (unsubdivide only)

    :type: int
    """

    ratio: float
    """ Ratio of triangles to reduce to (collapse only)

    :type: float
    """

    symmetry_axis: str
    """ Axis of symmetry

    :type: str
    """

    use_collapse_triangulate: bool
    """ Keep triangulated faces resulting from decimation (collapse only)

    :type: bool
    """

    use_dissolve_boundaries: bool
    """ Dissolve all vertices in between face boundaries (planar only)

    :type: bool
    """

    use_symmetry: bool
    """ Maintain symmetry on an axis

    :type: bool
    """

    vertex_group: str
    """ Vertex group name (collapse only)

    :type: str
    """

    vertex_group_factor: float
    """ Vertex group strength

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
