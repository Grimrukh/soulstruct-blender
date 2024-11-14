import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .nla_track import NlaTrack
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NlaTracks(bpy_prop_collection[NlaTrack], bpy_struct):
    """Collection of NLA Tracks"""

    active: NlaTrack | None
    """ Active NLA Track

    :type: NlaTrack | None
    """

    def new(self, prev: NlaTrack | None = None) -> NlaTrack:
        """Add a new NLA Track

        :param prev: NLA Track to add the new one after
        :type prev: NlaTrack | None
        :return: New NLA Track
        :rtype: NlaTrack
        """
        ...

    def remove(self, track: NlaTrack):
        """Remove a NLA Track

        :param track: NLA Track to remove
        :type track: NlaTrack
        """
        ...

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
