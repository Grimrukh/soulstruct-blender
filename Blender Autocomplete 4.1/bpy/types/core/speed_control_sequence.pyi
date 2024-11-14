import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .effect_sequence import EffectSequence

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpeedControlSequence(EffectSequence, Sequence, bpy_struct):
    """Sequence strip to control the speed of other strips"""

    input_1: Sequence
    """ First input for the effect strip

    :type: Sequence
    """

    input_count: int
    """ 

    :type: int
    """

    speed_control: str
    """ Speed control method

    :type: str
    """

    speed_factor: float
    """ Multiply the current speed of the sequence with this number or remap current frame to this frame

    :type: float
    """

    speed_frame_number: float
    """ Frame number of input strip

    :type: float
    """

    speed_length: float
    """ Percentage of input strip length

    :type: float
    """

    use_frame_interpolate: bool
    """ Do crossfade blending between current and next frame

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
