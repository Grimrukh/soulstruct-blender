import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .packed_file import PackedFile

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ImagePackedFile(bpy_struct):
    filepath: str
    """ 

    :type: str
    """

    packed_file: PackedFile
    """ 

    :type: PackedFile
    """

    tile_number: int
    """ 

    :type: int
    """

    view: int
    """ 

    :type: int
    """

    def save(self):
        """Save the packed file to its filepath"""
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
