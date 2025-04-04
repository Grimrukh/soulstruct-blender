import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .keying_set import KeyingSet

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyingSetsAll(bpy_prop_collection[KeyingSet], bpy_struct):
    """All available keying sets"""

    active: KeyingSet | None
    """ Active Keying Set used to insert/delete keyframes

    :type: KeyingSet | None
    """

    active_index: int | None
    """ Current Keying Set index (negative for 'builtin' and positive for 'absolute')

    :type: int | None
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
