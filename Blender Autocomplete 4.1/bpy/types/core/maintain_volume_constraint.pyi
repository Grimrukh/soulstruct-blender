import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaintainVolumeConstraint(Constraint, bpy_struct):
    """Maintain a constant volume along a single scaling axis"""

    free_axis: str
    """ The free scaling axis of the object

    :type: str
    """

    mode: str
    """ The way the constraint treats original non-free axis scaling

    :type: str
    """

    volume: float
    """ Volume of the bone at rest

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
