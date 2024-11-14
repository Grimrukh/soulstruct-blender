import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequencerToolSettings(bpy_struct):
    fit_method: str
    """ Scale fit method

    :type: str
    """

    overlap_mode: str
    """ How to resolve overlap after transformation

    :type: str
    """

    pivot_point: str
    """ Rotation or scaling pivot point

    :type: str
    """

    snap_distance: int
    """ Maximum distance for snapping in pixels

    :type: int
    """

    snap_ignore_muted: bool
    """ Don't snap to hidden strips

    :type: bool
    """

    snap_ignore_sound: bool
    """ Don't snap to sound strips

    :type: bool
    """

    snap_to_current_frame: bool
    """ Snap to current frame

    :type: bool
    """

    snap_to_hold_offset: bool
    """ Snap to strip hold offsets

    :type: bool
    """

    use_snap_current_frame_to_strips: bool
    """ Snap current frame to strip start or end

    :type: bool
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
