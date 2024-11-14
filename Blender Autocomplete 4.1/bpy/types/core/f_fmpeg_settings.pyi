import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FFmpegSettings(bpy_struct):
    """FFmpeg related settings for the scene"""

    audio_bitrate: int
    """ Audio bitrate (kb/s)

    :type: int
    """

    audio_channels: str
    """ Audio channel count

    :type: str
    """

    audio_codec: str
    """ FFmpeg audio codec to use

    :type: str
    """

    audio_mixrate: int
    """ Audio sample rate (samples/s)

    :type: int
    """

    audio_volume: float
    """ Audio volume

    :type: float
    """

    buffersize: int
    """ Rate control: buffer size (kb)

    :type: int
    """

    codec: str
    """ FFmpeg codec to use for video output

    :type: str
    """

    constant_rate_factor: str
    """ Constant Rate Factor (CRF); tradeoff between video quality and file size

    :type: str
    """

    ffmpeg_preset: str
    """ Tradeoff between encoding speed and compression ratio

    :type: str
    """

    format: str
    """ Output file container

    :type: str
    """

    gopsize: int
    """ Distance between key frames, also known as GOP size; influences file size and seekability

    :type: int
    """

    max_b_frames: int
    """ Maximum number of B-frames between non-B-frames; influences file size and seekability

    :type: int
    """

    maxrate: int
    """ Rate control: max rate (kbit/s)

    :type: int
    """

    minrate: int
    """ Rate control: min rate (kbit/s)

    :type: int
    """

    muxrate: int
    """ Mux rate (bits/second)

    :type: int
    """

    packetsize: int
    """ Mux packet size (byte)

    :type: int
    """

    use_autosplit: bool
    """ Autosplit output at 2GB boundary

    :type: bool
    """

    use_lossless_output: bool
    """ Use lossless output for video streams

    :type: bool
    """

    use_max_b_frames: bool
    """ Set a maximum number of B-frames

    :type: bool
    """

    video_bitrate: int
    """ Video bitrate (kbit/s)

    :type: int
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
