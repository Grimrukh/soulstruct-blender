import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .asset_tag import AssetTag
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AssetTags(bpy_prop_collection[AssetTag], bpy_struct):
    """Collection of custom asset tags"""

    def new(
        self, name: str | typing.Any, skip_if_exists: bool | typing.Any | None = False
    ) -> AssetTag:
        """Add a new tag to this asset

        :param name: Name
        :type name: str | typing.Any
        :param skip_if_exists: Skip if Exists, Do not add a new tag if one of the same type already exists
        :type skip_if_exists: bool | typing.Any | None
        :return: New tag
        :rtype: AssetTag
        """
        ...

    def remove(self, tag: AssetTag):
        """Remove an existing tag from this asset

        :param tag: Removed tag
        :type tag: AssetTag
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
