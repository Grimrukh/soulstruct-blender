import typing
import collections.abc
import mathutils
from .nla_strip import NlaStrip
from .bpy_prop_collection import bpy_prop_collection
from .action import Action
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NlaStrips(bpy_prop_collection[NlaStrip], bpy_struct):
    """Collection of NLA Strips"""

    def new(
        self, name: str | typing.Any, start: int | None, action: Action
    ) -> NlaStrip:
        """Add a new Action-Clip strip to the track

        :param name: Name for the NLA Strips
        :type name: str | typing.Any
        :param start: Start Frame, Start frame for this strip
        :type start: int | None
        :param action: Action to assign to this strip
        :type action: Action
        :return: New NLA Strip
        :rtype: NlaStrip
        """
        ...

    def remove(self, strip: NlaStrip):
        """Remove a NLA Strip

        :param strip: NLA Strip to remove
        :type strip: NlaStrip
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
