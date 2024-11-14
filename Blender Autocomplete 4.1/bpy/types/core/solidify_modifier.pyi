import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SolidifyModifier(Modifier, bpy_struct):
    """Create a solid skin, compensating for sharp angles"""

    bevel_convex: float
    """ Edge bevel weight to be added to outside edges

    :type: float
    """

    edge_crease_inner: float
    """ Assign a crease to inner edges

    :type: float
    """

    edge_crease_outer: float
    """ Assign a crease to outer edges

    :type: float
    """

    edge_crease_rim: float
    """ Assign a crease to the edges making up the rim

    :type: float
    """

    invert_vertex_group: bool
    """ Invert the vertex group influence

    :type: bool
    """

    material_offset: int
    """ Offset material index of generated faces

    :type: int
    """

    material_offset_rim: int
    """ Offset material index of generated rim faces

    :type: int
    """

    nonmanifold_boundary_mode: str
    """ Selects the boundary adjustment algorithm

    :type: str
    """

    nonmanifold_merge_threshold: float
    """ Distance within which degenerated geometry is merged

    :type: float
    """

    nonmanifold_thickness_mode: str
    """ Selects the used thickness algorithm

    :type: str
    """

    offset: float
    """ Offset the thickness from the center

    :type: float
    """

    rim_vertex_group: str
    """ Vertex group that the generated rim geometry will be weighted to

    :type: str
    """

    shell_vertex_group: str
    """ Vertex group that the generated shell geometry will be weighted to

    :type: str
    """

    solidify_mode: str
    """ Selects the used algorithm

    :type: str
    """

    thickness: float
    """ Thickness of the shell

    :type: float
    """

    thickness_clamp: float
    """ Offset clamp based on geometry scale

    :type: float
    """

    thickness_vertex_group: float
    """ Thickness factor to use for zero vertex group influence

    :type: float
    """

    use_even_offset: bool
    """ Maintain thickness by adjusting for sharp corners (slow, disable when not needed)

    :type: bool
    """

    use_flat_faces: bool
    """ Make faces use the minimal vertex weight assigned to their vertices (ensures new faces remain parallel to their original ones, slow, disable when not needed)

    :type: bool
    """

    use_flip_normals: bool
    """ Invert the face direction

    :type: bool
    """

    use_quality_normals: bool
    """ Calculate normals which result in more even thickness (slow, disable when not needed)

    :type: bool
    """

    use_rim: bool
    """ Create edge loops between the inner and outer surfaces on face edges (slow, disable when not needed)

    :type: bool
    """

    use_rim_only: bool
    """ Only add the rim to the original data

    :type: bool
    """

    use_thickness_angle_clamp: bool
    """ Clamp thickness based on angles

    :type: bool
    """

    vertex_group: str
    """ Vertex group name

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
