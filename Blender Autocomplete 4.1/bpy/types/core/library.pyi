import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .id import ID
from .packed_file import PackedFile

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Library(ID, bpy_struct):
    """External .blend file from which data is linked"""

    filepath: str
    """ Path to the library .blend file

    :type: str
    """

    needs_liboverride_resync: bool
    """ True if this library contains library overrides that are linked in current blendfile, and that had to be recursively resynced on load (it is recommended to open and re-save that library blendfile then)

    :type: bool
    """

    packed_file: PackedFile
    """ 

    :type: PackedFile
    """

    parent: Library
    """ 

    :type: Library
    """

    version: bpy_prop_array[int]
    """ Version of Blender the library .blend was saved with

    :type: bpy_prop_array[int]
    """

    users_id: typing.Any
    """ ID data blocks which use this library(readonly)"""

    def reload(self):
        """Reload this library and all its linked data-blocks"""
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
