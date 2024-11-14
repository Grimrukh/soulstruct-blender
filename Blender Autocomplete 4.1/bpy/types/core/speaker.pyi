import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .anim_data import AnimData
from .id import ID
from .sound import Sound

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Speaker(ID, bpy_struct):
    """Speaker data-block for 3D audio speaker objects"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    attenuation: float
    """ How strong the distance affects volume, depending on distance model

    :type: float
    """

    cone_angle_inner: float
    """ Angle of the inner cone, in degrees, inside the cone the volume is 100%

    :type: float
    """

    cone_angle_outer: float
    """ Angle of the outer cone, in degrees, outside this cone the volume is the outer cone volume, between inner and outer cone the volume is interpolated

    :type: float
    """

    cone_volume_outer: float
    """ Volume outside the outer cone

    :type: float
    """

    distance_max: float
    """ Maximum distance for volume calculation, no matter how far away the object is

    :type: float
    """

    distance_reference: float
    """ Reference distance at which volume is 100%

    :type: float
    """

    muted: bool
    """ Mute the speaker

    :type: bool
    """

    pitch: float
    """ Playback pitch of the sound

    :type: float
    """

    sound: Sound
    """ Sound data-block used by this speaker

    :type: Sound
    """

    volume: float
    """ How loud the sound is

    :type: float
    """

    volume_max: float
    """ Maximum volume, no matter how near the object is

    :type: float
    """

    volume_min: float
    """ Minimum volume, no matter how far away the object is

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
