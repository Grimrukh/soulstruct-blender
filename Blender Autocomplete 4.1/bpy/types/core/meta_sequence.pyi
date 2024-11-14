import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .sequences_meta import SequencesMeta
from .struct import Struct
from .sequence_transform import SequenceTransform
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .sequence_timeline_channel import SequenceTimelineChannel
from .sequence_proxy import SequenceProxy
from .sequence_crop import SequenceCrop

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MetaSequence(Sequence, bpy_struct):
    """Sequence strip to group other strips as a single sequence strip"""

    alpha_mode: str
    """ Representation of alpha information in the RGBA pixels

    :type: str
    """

    animation_offset_end: int
    """ Animation end offset (trim end)

    :type: int
    """

    animation_offset_start: int
    """ Animation start offset (trim start)

    :type: int
    """

    channels: bpy_prop_collection[SequenceTimelineChannel]
    """ 

    :type: bpy_prop_collection[SequenceTimelineChannel]
    """

    color_multiply: float
    """ 

    :type: float
    """

    color_saturation: float
    """ Adjust the intensity of the input's color

    :type: float
    """

    crop: SequenceCrop
    """ 

    :type: SequenceCrop
    """

    multiply_alpha: bool
    """ Multiply alpha along with color channels

    :type: bool
    """

    proxy: SequenceProxy
    """ 

    :type: SequenceProxy
    """

    sequences: SequencesMeta
    """ Sequences nested in meta strip

    :type: SequencesMeta
    """

    strobe: float
    """ Only display every nth frame

    :type: float
    """

    transform: SequenceTransform
    """ 

    :type: SequenceTransform
    """

    use_deinterlace: bool
    """ Remove fields from video movies

    :type: bool
    """

    use_flip_x: bool
    """ Flip on the X axis

    :type: bool
    """

    use_flip_y: bool
    """ Flip on the Y axis

    :type: bool
    """

    use_float: bool
    """ Convert input to float data

    :type: bool
    """

    use_proxy: bool
    """ Use a preview proxy and/or time-code index for this strip

    :type: bool
    """

    use_reverse_frames: bool
    """ Reverse frame order

    :type: bool
    """

    def separate(self):
        """Separate meta"""
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
