import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .asset_meta_data import AssetMetaData

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FileSelectEntry(bpy_struct):
    """A file viewable in the File Browser"""

    asset_data: AssetMetaData
    """ Asset data, valid if the file represents an asset

    :type: AssetMetaData
    """

    name: str
    """ 

    :type: str
    """

    preview_icon_id: int
    """ Unique integer identifying the preview of this file as an icon (zero means invalid)

    :type: int
    """

    relative_path: str
    """ Path relative to the directory currently displayed in the File Browser (includes the file name)

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
