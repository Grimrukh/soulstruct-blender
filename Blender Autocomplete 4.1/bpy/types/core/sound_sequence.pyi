import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .sound import Sound

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SoundSequence(Sequence, bpy_struct):
    """Sequence strip defining a sound to be played over a period of time"""

    animation_offset_end: int
    """ Animation end offset (trim end)

    :type: int
    """

    animation_offset_start: int
    """ Animation start offset (trim start)

    :type: int
    """

    pan: float
    """ Playback panning of the sound (only for Mono sources)

    :type: float
    """

    show_waveform: bool
    """ Display the audio waveform inside the strip

    :type: bool
    """

    sound: Sound
    """ Sound data-block used by this sequence

    :type: Sound
    """

    volume: float
    """ Playback volume of the sound

    :type: float
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
