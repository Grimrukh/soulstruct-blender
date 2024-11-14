import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .keying_set import KeyingSet

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyingSets(bpy_prop_collection[KeyingSet], bpy_struct):
    """Scene keying sets"""

    active: KeyingSet | None
    """ Active Keying Set used to insert/delete keyframes

    :type: KeyingSet | None
    """

    active_index: int | None
    """ Current Keying Set index (negative for 'builtin' and positive for 'absolute')

    :type: int | None
    """

    def new(
        self,
        idname: str | typing.Any = "KeyingSet",
        name: str | typing.Any = "KeyingSet",
    ) -> KeyingSet:
        """Add a new Keying Set to Scene

        :param idname: IDName, Internal identifier of Keying Set
        :type idname: str | typing.Any
        :param name: Name, User visible name of Keying Set
        :type name: str | typing.Any
        :return: Newly created Keying Set
        :rtype: KeyingSet
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
