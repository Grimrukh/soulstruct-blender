import typing
import collections.abc
import mathutils
from .struct import Struct
from .file_asset_select_id_filter import FileAssetSelectIDFilter
from .file_select_params import FileSelectParams
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FileAssetSelectParams(FileSelectParams, bpy_struct):
    """Settings for the file selection in Asset Browser mode"""

    asset_library_reference: str
    """ 

    :type: str
    """

    catalog_id: str
    """ The UUID of the catalog shown in the browser

    :type: str
    """

    filter_asset_id: FileAssetSelectIDFilter
    """ Which asset types to show/hide, when browsing an asset library

    :type: FileAssetSelectIDFilter
    """

    import_method: str
    """ Determine how the asset will be imported

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
