import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .asset_meta_data import AssetMetaData

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AssetRepresentation(bpy_struct):
    """Information about an entity that makes it possible for the asset system to deal with the entity as asset"""

    full_library_path: str
    """ Absolute path to the .blend file containing this asset

    :type: str
    """

    full_path: str
    """ Absolute path to the .blend file containing this asset extended with the path of the asset inside the file

    :type: str
    """

    id_type: str
    """ The type of the data-block, if the asset represents one ('NONE' otherwise)

    :type: str
    """

    local_id: ID
    """ The local data-block this asset represents; only valid if that is a data-block in this file

    :type: ID
    """

    metadata: AssetMetaData
    """ Additional information about the asset

    :type: AssetMetaData
    """

    name: str
    """ 

    :type: str
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
