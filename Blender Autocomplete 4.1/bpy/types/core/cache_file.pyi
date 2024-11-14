import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .cache_object_paths import CacheObjectPaths
from .anim_data import AnimData
from .id import ID
from .cache_file_layers import CacheFileLayers

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CacheFile(ID, bpy_struct):
    active_index: int | None
    """ 

    :type: int | None
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    filepath: str
    """ Path to external displacements file

    :type: str
    """

    forward_axis: str
    """ 

    :type: str
    """

    frame: float
    """ The time to use for looking up the data in the cache file, or to determine which file to use in a file sequence

    :type: float
    """

    frame_offset: float
    """ Subtracted from the current frame to use for looking up the data in the cache file, or to determine which file to use in a file sequence

    :type: float
    """

    is_sequence: bool
    """ Whether the cache is separated in a series of files

    :type: bool
    """

    layers: CacheFileLayers
    """ Layers of the cache

    :type: CacheFileLayers
    """

    object_paths: CacheObjectPaths
    """ Paths of the objects inside the Alembic archive

    :type: CacheObjectPaths
    """

    override_frame: bool
    """ Whether to use a custom frame for looking up data in the cache file, instead of using the current scene frame

    :type: bool
    """

    prefetch_cache_size: int
    """ Memory usage limit in megabytes for the Cycles Procedural cache, if the data does not fit within the limit, rendering is aborted

    :type: int
    """

    scale: float
    """ Value by which to enlarge or shrink the object with respect to the world's origin (only applicable through a Transform Cache constraint)

    :type: float
    """

    up_axis: str
    """ 

    :type: str
    """

    use_prefetch: bool
    """ When enabled, the Cycles Procedural will preload animation data for faster updates

    :type: bool
    """

    use_render_procedural: bool
    """ Display boxes in the viewport as placeholders for the objects, Cycles will use a procedural to load the objects during viewport rendering in experimental mode, other render engines will also receive a placeholder and should take care of loading the Alembic data themselves if possible

    :type: bool
    """

    velocity_name: str
    """ Name of the Alembic attribute used for generating motion blur data

    :type: str
    """

    velocity_unit: str
    """ Define how the velocity vectors are interpreted with regard to time, 'frame' means the delta time is 1 frame, 'second' means the delta time is 1 / FPS

    :type: str
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
