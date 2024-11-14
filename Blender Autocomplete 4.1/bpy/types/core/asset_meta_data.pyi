import typing
import collections.abc
import mathutils
from .struct import Struct
from .asset_tags import AssetTags
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AssetMetaData(bpy_struct):
    """Additional data stored for an asset data-block"""

    active_tag: int | None
    """ Index of the tag set for editing

    :type: int | None
    """

    author: str
    """ Name of the creator of the asset

    :type: str
    """

    catalog_id: str
    """ Identifier for the asset's catalog, used by Blender to look up the asset's catalog path. Must be a UUID according to RFC4122

    :type: str
    """

    catalog_simple_name: str
    """ Simple name of the asset's catalog, for debugging and data recovery purposes

    :type: str
    """

    copyright: str
    """ Copyright notice for this asset. An empty copyright notice does not necessarily indicate that this is copyright-free. Contact the author if any clarification is needed

    :type: str
    """

    description: str
    """ A description of the asset to be displayed for the user

    :type: str
    """

    license: str
    """ The type of license this asset is distributed under. An empty license name does not necessarily indicate that this is free of licensing terms. Contact the author if any clarification is needed

    :type: str
    """

    tags: AssetTags
    """ Custom tags (name tokens) for the asset, used for filtering and general asset management

    :type: AssetTags
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
