import typing
import collections.abc
import mathutils
from .struct import Struct
from .sequence_transform import SequenceTransform
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .sequence_proxy import SequenceProxy
from .sequence_crop import SequenceCrop
from .object import Object
from .scene import Scene

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SceneSequence(Sequence, bpy_struct):
    """Sequence strip using the rendered image of a scene"""

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

    crop: SequenceCrop
    """ 

    :type: SequenceCrop
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

    scene: Scene
    """ Scene that this sequence uses

    :type: Scene
    """

    scene_camera: Object
    """ Override the scene's active camera

    :type: Object
    """

    scene_input: str
    """ Input type to use for the Scene strip

    :type: str
    """

    strobe: float
    """ Only display every nth frame

    :type: float
    """

    transform: SequenceTransform
    """ 

    :type: SequenceTransform
    """

    use_annotations: bool
    """ Show Annotations in OpenGL previews

    :type: bool
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
