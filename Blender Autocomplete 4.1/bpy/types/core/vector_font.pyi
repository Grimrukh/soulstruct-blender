import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .packed_file import PackedFile

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VectorFont(ID, bpy_struct):
    """Vector font for Text objects"""

    filepath: str
    """ 

    :type: str
    """

    packed_file: PackedFile
    """ 

    :type: PackedFile
    """

    def pack(self):
        """Pack the font into the current blend file"""
        ...

    def unpack(self, method: str | None = "USE_LOCAL"):
        """Unpack the font to the samples filename

        :param method: method, How to unpack
        :type method: str | None
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
