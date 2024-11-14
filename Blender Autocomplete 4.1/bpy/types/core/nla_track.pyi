import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .nla_strips import NlaStrips

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NlaTrack(bpy_struct):
    """An animation layer containing Actions referenced as NLA strips"""

    active: bool
    """ NLA Track is active

    :type: bool
    """

    is_override_data: bool
    """ In a local override data, whether this NLA track comes from the linked reference data, or is local to the override

    :type: bool
    """

    is_solo: bool
    """ NLA Track is evaluated itself (i.e. active Action and all other NLA Tracks in the same AnimData block are disabled)

    :type: bool
    """

    lock: bool
    """ NLA Track is locked

    :type: bool
    """

    mute: bool
    """ Disable NLA Track evaluation

    :type: bool
    """

    name: str
    """ 

    :type: str
    """

    select: bool
    """ NLA Track is selected

    :type: bool
    """

    strips: NlaStrips
    """ NLA Strips on this NLA-track

    :type: NlaStrips
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
