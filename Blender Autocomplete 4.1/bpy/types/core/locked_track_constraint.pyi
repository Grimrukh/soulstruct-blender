import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LockedTrackConstraint(Constraint, bpy_struct):
    """Point toward the target along the track axis, while locking the other axis"""

    head_tail: float
    """ Target along length of bone: Head is 0, Tail is 1

    :type: float
    """

    lock_axis: str
    """ Axis that points upward

    :type: str
    """

    subtarget: str
    """ Armature bone, mesh or lattice vertex group, ...

    :type: str
    """

    target: Object
    """ Target object

    :type: Object
    """

    track_axis: str
    """ Axis that points to the target object

    :type: str
    """

    use_bbone_shape: bool
    """ Follow shape of B-Bone segments when calculating Head/Tail position

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
