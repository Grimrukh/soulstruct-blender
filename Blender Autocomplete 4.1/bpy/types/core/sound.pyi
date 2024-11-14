import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .packed_file import PackedFile

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Sound(ID, bpy_struct):
    """Sound data-block referencing an external or packed sound file"""

    channels: str
    """ Definition of audio channels

    :type: str
    """

    filepath: str
    """ Sound sample file used by this Sound data-block

    :type: str
    """

    packed_file: PackedFile
    """ 

    :type: PackedFile
    """

    samplerate: int
    """ Sample rate of the audio in Hz

    :type: int
    """

    use_memory_cache: bool
    """ The sound file is decoded and loaded into RAM

    :type: bool
    """

    use_mono: bool
    """ If the file contains multiple audio channels they are rendered to a single one

    :type: bool
    """

    factory: typing.Any
    """ The aud.Factory object of the sound.(readonly)"""

    def pack(self):
        """Pack the sound into the current blend file"""
        ...

    def unpack(self, method: str | None = "USE_LOCAL"):
        """Unpack the sound to the samples filename

        :param method: method, How to unpack
        :type method: str | None
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
