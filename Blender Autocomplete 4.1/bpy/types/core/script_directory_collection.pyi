import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .script_directory import ScriptDirectory

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ScriptDirectoryCollection(bpy_prop_collection[ScriptDirectory], bpy_struct):
    @classmethod
    def new(cls) -> ScriptDirectory:
        """Add a new Python script directory

        :return:
        :rtype: ScriptDirectory
        """
        ...

    @classmethod
    def remove(cls, script_directory: ScriptDirectory):
        """Remove a Python script directory

        :param script_directory:
        :type script_directory: ScriptDirectory
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
