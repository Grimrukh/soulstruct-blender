import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequencerTimelineOverlay(bpy_struct):
    show_fcurves: bool
    """ Display strip opacity/volume curve

    :type: bool
    """

    show_grid: bool
    """ Show vertical grid lines

    :type: bool
    """

    show_strip_duration: bool
    """ 

    :type: bool
    """

    show_strip_name: bool
    """ 

    :type: bool
    """

    show_strip_offset: bool
    """ Display strip in/out offsets

    :type: bool
    """

    show_strip_retiming: bool
    """ Display retiming keys on top of strips

    :type: bool
    """

    show_strip_source: bool
    """ Display path to source file, or name of source datablock

    :type: bool
    """

    show_strip_tag_color: bool
    """ Display the strip color tags in the sequencer

    :type: bool
    """

    show_thumbnails: bool
    """ Show strip thumbnails

    :type: bool
    """

    waveform_display_style: str
    """ How Waveforms are displayed

    :type: str
    """

    waveform_display_type: str
    """ How Waveforms are displayed

    :type: str
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
