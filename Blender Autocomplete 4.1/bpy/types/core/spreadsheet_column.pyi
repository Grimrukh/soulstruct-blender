import typing
import collections.abc
import mathutils
from .struct import Struct
from .spreadsheet_column_id import SpreadsheetColumnID
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpreadsheetColumn(bpy_struct):
    """Persistent data associated with a spreadsheet column"""

    data_type: str
    """ The data type of the corresponding column visible in the spreadsheet

    :type: str
    """

    id: SpreadsheetColumnID
    """ Data used to identify the corresponding data from the data source

    :type: SpreadsheetColumnID
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
