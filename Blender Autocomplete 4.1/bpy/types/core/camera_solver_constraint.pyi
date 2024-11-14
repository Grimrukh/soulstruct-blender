import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .movie_clip import MovieClip

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CameraSolverConstraint(Constraint, bpy_struct):
    """Lock motion to the reconstructed camera movement"""

    clip: MovieClip
    """ Movie Clip to get tracking data from

    :type: MovieClip
    """

    use_active_clip: bool
    """ Use active clip defined in scene

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
