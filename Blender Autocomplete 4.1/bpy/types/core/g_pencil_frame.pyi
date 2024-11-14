import typing
import collections.abc
import mathutils
from .struct import Struct
from .g_pencil_strokes import GPencilStrokes
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilFrame(bpy_struct):
    """Collection of related sketches on a particular frame"""

    frame_number: int
    """ The frame on which this sketch appears

    :type: int
    """

    is_edited: bool
    """ Frame is being edited (painted on)

    :type: bool
    """

    keyframe_type: str
    """ Type of keyframe

    :type: str
    """

    select: bool
    """ Frame is selected for editing in the Dope Sheet

    :type: bool
    """

    strokes: GPencilStrokes
    """ Freehand curves defining the sketch on this frame

    :type: GPencilStrokes
    """

    def clear(self):
        """Remove all the grease pencil frame data"""
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
