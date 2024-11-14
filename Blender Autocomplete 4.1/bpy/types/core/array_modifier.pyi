import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ArrayModifier(Modifier, bpy_struct):
    """Array duplication modifier"""

    constant_offset_displace: mathutils.Vector
    """ Value for the distance between arrayed items

    :type: mathutils.Vector
    """

    count: int
    """ Number of duplicates to make

    :type: int
    """

    curve: Object
    """ Curve object to fit array length to

    :type: Object
    """

    end_cap: Object
    """ Mesh object to use as an end cap

    :type: Object
    """

    fit_length: float
    """ Length to fit array within

    :type: float
    """

    fit_type: str
    """ Array length calculation method

    :type: str
    """

    merge_threshold: float
    """ Limit below which to merge vertices

    :type: float
    """

    offset_object: Object
    """ Use the location and rotation of another object to determine the distance and rotational change between arrayed items

    :type: Object
    """

    offset_u: float
    """ Amount to offset array UVs on the U axis

    :type: float
    """

    offset_v: float
    """ Amount to offset array UVs on the V axis

    :type: float
    """

    relative_offset_displace: mathutils.Vector
    """ The size of the geometry will determine the distance between arrayed items

    :type: mathutils.Vector
    """

    start_cap: Object
    """ Mesh object to use as a start cap

    :type: Object
    """

    use_constant_offset: bool
    """ Add a constant offset

    :type: bool
    """

    use_merge_vertices: bool
    """ Merge vertices in adjacent duplicates

    :type: bool
    """

    use_merge_vertices_cap: bool
    """ Merge vertices in first and last duplicates

    :type: bool
    """

    use_object_offset: bool
    """ Add another object's transformation to the total offset

    :type: bool
    """

    use_relative_offset: bool
    """ Add an offset relative to the object's bounding box

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
