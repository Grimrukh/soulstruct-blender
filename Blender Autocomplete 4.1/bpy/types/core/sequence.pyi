import typing
import collections.abc
import mathutils
from .sequence_modifiers import SequenceModifiers
from .sequence_element import SequenceElement
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Sequence(bpy_struct):
    """Sequence strip in the sequence editor"""

    blend_alpha: float
    """ Percentage of how much the strip's colors affect other strips

    :type: float
    """

    blend_type: str
    """ Method for controlling how the strip combines with other strips

    :type: str
    """

    channel: int
    """ Y position of the sequence strip

    :type: int
    """

    color_tag: str
    """ Color tag for a strip

    :type: str
    """

    effect_fader: float
    """ Custom fade value

    :type: float
    """

    frame_duration: int
    """ The length of the contents of this strip before the handles are applied

    :type: int
    """

    frame_final_duration: int
    """ The length of the contents of this strip after the handles are applied

    :type: int
    """

    frame_final_end: int
    """ End frame displayed in the sequence editor after offsets are applied

    :type: int
    """

    frame_final_start: int
    """ Start frame displayed in the sequence editor after offsets are applied, setting this is equivalent to moving the handle, not the actual start frame

    :type: int
    """

    frame_offset_end: float
    """ 

    :type: float
    """

    frame_offset_start: float
    """ 

    :type: float
    """

    frame_start: float
    """ X position where the strip begins

    :type: float
    """

    lock: bool
    """ Lock strip so that it cannot be transformed

    :type: bool
    """

    modifiers: SequenceModifiers
    """ Modifiers affecting this strip

    :type: SequenceModifiers
    """

    mute: bool
    """ Disable strip so that it cannot be viewed in the output

    :type: bool
    """

    name: str
    """ 

    :type: str
    """

    override_cache_settings: bool
    """ Override global cache settings

    :type: bool
    """

    select: bool
    """ 

    :type: bool
    """

    select_left_handle: bool
    """ 

    :type: bool
    """

    select_right_handle: bool
    """ 

    :type: bool
    """

    show_retiming_keys: bool
    """ Show retiming keys, so they can be moved

    :type: bool
    """

    type: str
    """ 

    :type: str
    """

    use_cache_composite: bool
    """ Cache intermediate composited images, for faster tweaking of stacked strips at the cost of memory usage

    :type: bool
    """

    use_cache_preprocessed: bool
    """ Cache preprocessed images, for faster tweaking of effects at the cost of memory usage

    :type: bool
    """

    use_cache_raw: bool
    """ Cache raw images read from disk, for faster tweaking of strip parameters at the cost of memory usage

    :type: bool
    """

    use_default_fade: bool
    """ Fade effect using the built-in default (usually make transition as long as effect strip)

    :type: bool
    """

    use_linear_modifiers: bool
    """ Calculate modifiers in linear space instead of sequencer's space

    :type: bool
    """

    def strip_elem_from_frame(self, frame: int | None) -> SequenceElement:
        """Return the strip element from a given frame or None

        :param frame: Frame, The frame to get the strip element from
        :type frame: int | None
        :return: strip element of the current frame
        :rtype: SequenceElement
        """
        ...

    def swap(self, other: Sequence):
        """swap

        :param other: Other
        :type other: Sequence
        """
        ...

    def move_to_meta(self, meta_sequence: Sequence):
        """move_to_meta

        :param meta_sequence: Destination Meta Sequence, Meta to move the strip into
        :type meta_sequence: Sequence
        """
        ...

    def parent_meta(self) -> Sequence:
        """Parent meta

        :return: Parent Meta
        :rtype: Sequence
        """
        ...

    def invalidate_cache(self, type: str):
        """Invalidate cached images for strip and all dependent strips

        :param type: Type, Cache Type
        :type type: str
        """
        ...

    def split(self, frame: int | None, split_method: str) -> Sequence:
        """Split Sequence

        :param frame: Frame where to split the strip
        :type frame: int | None
        :param split_method:
        :type split_method: str
        :return: Right side Sequence
        :rtype: Sequence
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
