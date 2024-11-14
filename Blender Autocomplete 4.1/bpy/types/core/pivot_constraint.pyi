import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PivotConstraint(Constraint, bpy_struct):
    """Rotate around a different point"""

    head_tail: float
    """ Target along length of bone: Head is 0, Tail is 1

    :type: float
    """

    offset: mathutils.Vector
    """ Offset of pivot from target (when set), or from owner's location (when Fixed Position is off), or the absolute pivot point

    :type: mathutils.Vector
    """

    rotation_range: str
    """ Rotation range on which pivoting should occur

    :type: str
    """

    subtarget: str
    """ 

    :type: str
    """

    target: Object
    """ Target Object, defining the position of the pivot when defined

    :type: Object
    """

    use_bbone_shape: bool
    """ Follow shape of B-Bone segments when calculating Head/Tail position

    :type: bool
    """

    use_relative_location: bool
    """ Offset will be an absolute point in space instead of relative to the target

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
