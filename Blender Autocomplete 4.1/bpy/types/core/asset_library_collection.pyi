import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .user_asset_library import UserAssetLibrary
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AssetLibraryCollection(bpy_prop_collection[UserAssetLibrary], bpy_struct):
    """Collection of user asset libraries"""

    @classmethod
    def new(
        cls, name: str | typing.Any = "", directory: str | typing.Any = ""
    ) -> UserAssetLibrary:
        """Add a new Asset Library

        :param name: Name
        :type name: str | typing.Any
        :param directory: Directory
        :type directory: str | typing.Any
        :return: Newly added asset library
        :rtype: UserAssetLibrary
        """
        ...

    @classmethod
    def remove(cls, library: UserAssetLibrary):
        """Remove an Asset Library

        :param library:
        :type library: UserAssetLibrary
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
