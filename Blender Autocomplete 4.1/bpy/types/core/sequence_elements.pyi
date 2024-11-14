import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .sequence_element import SequenceElement
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequenceElements(bpy_prop_collection[SequenceElement], bpy_struct):
    """Collection of SequenceElement"""

    def append(self, filename: str | typing.Any) -> SequenceElement:
        """Push an image from ImageSequence.directory

        :param filename: Filepath to image
        :type filename: str | typing.Any
        :return: New SequenceElement
        :rtype: SequenceElement
        """
        ...

    def pop(self, index: int | None):
        """Pop an image off the collection

        :param index: Index of image to remove
        :type index: int | None
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
