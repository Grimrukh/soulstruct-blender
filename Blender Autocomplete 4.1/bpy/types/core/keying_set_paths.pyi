import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .keying_set_path import KeyingSetPath
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyingSetPaths(bpy_prop_collection[KeyingSetPath], bpy_struct):
    """Collection of keying set paths"""

    active: KeyingSetPath | None
    """ Active Keying Set used to insert/delete keyframes

    :type: KeyingSetPath | None
    """

    active_index: int | None
    """ Current Keying Set index

    :type: int | None
    """

    def add(
        self,
        target_id: ID | None,
        data_path: str | typing.Any,
        index: typing.Any | None = -1,
        group_method: str | None = "KEYINGSET",
        group_name: str | typing.Any = "",
    ) -> KeyingSetPath:
        """Add a new path for the Keying Set

        :param target_id: Target ID, ID data-block for the destination
        :type target_id: ID | None
        :param data_path: Data-Path, RNA-Path to destination property
        :type data_path: str | typing.Any
        :param index: Index, The index of the destination property (i.e. axis of Location/Rotation/etc.), or -1 for the entire array
        :type index: typing.Any | None
        :param group_method: Grouping Method, Method used to define which Group-name to use
        :type group_method: str | None
        :param group_name: Group Name, Name of Action Group to assign destination to (only if grouping mode is to use this name)
        :type group_name: str | typing.Any
        :return: New Path, Path created and added to the Keying Set
        :rtype: KeyingSetPath
        """
        ...

    def remove(self, path: KeyingSetPath):
        """Remove the given path from the Keying Set

        :param path: Path
        :type path: KeyingSetPath
        """
        ...

    def clear(self):
        """Remove all the paths from the Keying Set"""
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
