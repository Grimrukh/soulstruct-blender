import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .retiming_keys import RetimingKeys
from .struct import Struct
from .sequence_element import SequenceElement
from .color_managed_input_colorspace_settings import ColorManagedInputColorspaceSettings
from .stereo3d_format import Stereo3dFormat
from .sequence_transform import SequenceTransform
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .sequence_proxy import SequenceProxy
from .sequence_crop import SequenceCrop
from .id_property_wrap_ptr import IDPropertyWrapPtr

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieSequence(Sequence, bpy_struct):
    """Sequence strip to load a video"""

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

    color_multiply: float
    """ 

    :type: float
    """

    color_saturation: float
    """ Adjust the intensity of the input's color

    :type: float
    """

    colorspace_settings: ColorManagedInputColorspaceSettings
    """ Input color space settings

    :type: ColorManagedInputColorspaceSettings
    """

    crop: SequenceCrop
    """ 

    :type: SequenceCrop
    """

    elements: bpy_prop_collection[SequenceElement]
    """ 

    :type: bpy_prop_collection[SequenceElement]
    """

    filepath: str
    """ 

    :type: str
    """

    fps: float
    """ Frames per second

    :type: float
    """

    multiply_alpha: bool
    """ Multiply alpha along with color channels

    :type: bool
    """

    proxy: SequenceProxy
    """ 

    :type: SequenceProxy
    """

    retiming_keys: RetimingKeys
    """ 

    :type: RetimingKeys
    """

    stereo_3d_format: Stereo3dFormat
    """ Settings for stereo 3D

    :type: Stereo3dFormat
    """

    stream_index: int
    """ For files with several movie streams, use the stream with the given index

    :type: int
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

    use_multiview: bool
    """ Use Multiple Views (when available)

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

    views_format: str
    """ Mode to load movie views

    :type: str
    """

    def reload_if_needed(self) -> bool:
        """reload_if_needed

        :return: True if the strip can produce frames, False otherwise
        :rtype: bool
        """
        ...

    def metadata(self) -> IDPropertyWrapPtr:
        """Retrieve metadata of the movie file

        :return: Dict-like object containing the metadata
        :rtype: IDPropertyWrapPtr
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
