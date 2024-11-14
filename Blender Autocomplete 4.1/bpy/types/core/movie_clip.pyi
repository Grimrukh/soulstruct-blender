import typing
import collections.abc
import mathutils
from .color_managed_input_colorspace_settings import ColorManagedInputColorspaceSettings
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .anim_data import AnimData
from .id import ID
from .movie_tracking import MovieTracking
from .movie_clip_proxy import MovieClipProxy
from .grease_pencil import GreasePencil
from .id_property_wrap_ptr import IDPropertyWrapPtr

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieClip(ID, bpy_struct):
    """MovieClip data-block referencing an external movie file"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    colorspace_settings: ColorManagedInputColorspaceSettings
    """ Input color space settings

    :type: ColorManagedInputColorspaceSettings
    """

    display_aspect: mathutils.Vector
    """ Display Aspect for this clip, does not affect rendering

    :type: mathutils.Vector
    """

    filepath: str
    """ Filename of the movie or sequence file

    :type: str
    """

    fps: float
    """ Detected frame rate of the movie clip in frames per second

    :type: float
    """

    frame_duration: int
    """ Detected duration of movie clip in frames

    :type: int
    """

    frame_offset: int
    """ Offset of footage first frame relative to its file name (affects only how footage is loading, does not change data associated with a clip)

    :type: int
    """

    frame_start: int
    """ Global scene frame number at which this movie starts playing (affects all data associated with a clip)

    :type: int
    """

    grease_pencil: GreasePencil
    """ Grease pencil data for this movie clip

    :type: GreasePencil
    """

    proxy: MovieClipProxy
    """ 

    :type: MovieClipProxy
    """

    size: bpy_prop_array[int]
    """ Width and height in pixels, zero when image data can't be loaded

    :type: bpy_prop_array[int]
    """

    source: str
    """ Where the clip comes from

    :type: str
    """

    tracking: MovieTracking
    """ 

    :type: MovieTracking
    """

    use_proxy: bool
    """ Use a preview proxy and/or timecode index for this clip

    :type: bool
    """

    use_proxy_custom_directory: bool
    """ Create proxy images in a custom directory (default is movie location)

    :type: bool
    """

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
