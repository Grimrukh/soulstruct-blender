import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .time_gpencil_modifier_segment import TimeGpencilModifierSegment
from .struct import Struct
from .bpy_struct import bpy_struct
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TimeGpencilModifier(GpencilModifier, bpy_struct):
    """Time offset modifier"""

    frame_end: int
    """ Final frame of the range

    :type: int
    """

    frame_scale: float
    """ Evaluation time in seconds

    :type: float
    """

    frame_start: int
    """ First frame of the range

    :type: int
    """

    invert_layer_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_layers: bool
    """ Inverse filter

    :type: bool
    """

    layer: str
    """ Layer name

    :type: str
    """

    layer_pass: int
    """ Layer pass index

    :type: int
    """

    mode: str
    """ 

    :type: str
    """

    offset: int
    """ Number of frames to offset original keyframe number or frame to fix

    :type: int
    """

    segment_active_index: int
    """ Active index in the segment list

    :type: int
    """

    segments: bpy_prop_collection[TimeGpencilModifierSegment]
    """ 

    :type: bpy_prop_collection[TimeGpencilModifierSegment]
    """

    use_custom_frame_range: bool
    """ Define a custom range of frames to use in modifier

    :type: bool
    """

    use_keep_loop: bool
    """ Retiming end frames and move to start of animation to keep loop

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
