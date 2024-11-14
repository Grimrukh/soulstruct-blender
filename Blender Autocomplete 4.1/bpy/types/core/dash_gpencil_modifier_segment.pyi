import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DashGpencilModifierSegment(bpy_struct):
    """Configuration for a single dash segment"""

    dash: int
    """ The number of consecutive points from the original stroke to include in this segment

    :type: int
    """

    gap: int
    """ The number of points skipped after this segment

    :type: int
    """

    material_index: int
    """ Use this index on generated segment. -1 means using the existing material

    :type: int
    """

    name: str
    """ Name of the dash segment

    :type: str
    """

    opacity: float
    """ The factor to apply to the original point's opacity for the new points

    :type: float
    """

    radius: float
    """ The factor to apply to the original point's radius for the new points

    :type: float
    """

    use_cyclic: bool
    """ Enable cyclic on individual stroke dashes

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
