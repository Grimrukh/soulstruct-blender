import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .user_solid_light import UserSolidLight
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PreferencesSystem(bpy_struct):
    """Graphics driver and operating system settings"""

    anisotropic_filter: str
    """ Quality of anisotropic filtering

    :type: str
    """

    audio_channels: str
    """ Audio channel count

    :type: str
    """

    audio_device: str
    """ Audio output device

    :type: str
    """

    audio_mixing_buffer: str
    """ Number of samples used by the audio mixing buffer

    :type: str
    """

    audio_sample_format: str
    """ Audio sample format

    :type: str
    """

    audio_sample_rate: str
    """ Audio sample rate

    :type: str
    """

    dpi: int
    """ 

    :type: int
    """

    gl_clip_alpha: float
    """ Clip alpha below this threshold in the 3D textured view

    :type: float
    """

    gl_texture_limit: str
    """ Limit the texture size to save graphics memory

    :type: str
    """

    gpu_backend: str
    """ GPU backend to use (requires restarting Blender for changes to take effect)

    :type: str
    """

    image_draw_method: str
    """ Method used for displaying images on the screen

    :type: str
    """

    is_microsoft_store_install: bool
    """ Whether this blender installation is a sandboxed Microsoft Store version

    :type: bool
    """

    legacy_compute_device_type: int
    """ For backwards compatibility only

    :type: int
    """

    light_ambient: mathutils.Color
    """ Color of the ambient light that uniformly lit the scene

    :type: mathutils.Color
    """

    memory_cache_limit: int
    """ Memory cache limit (in megabytes)

    :type: int
    """

    pixel_size: float
    """ 

    :type: float
    """

    register_all_users: bool
    """ Make this Blender version open blend files for all users. Requires elevated privileges

    :type: bool
    """

    scrollback: int
    """ Maximum number of lines to store for the console buffer

    :type: int
    """

    sequencer_disk_cache_compression: str
    """ Smaller compression will result in larger files, but less decoding overhead

    :type: str
    """

    sequencer_disk_cache_dir: str
    """ Override default directory

    :type: str
    """

    sequencer_disk_cache_size_limit: int
    """ Disk cache limit (in gigabytes)

    :type: int
    """

    sequencer_proxy_setup: str
    """ When and how proxies are created

    :type: str
    """

    solid_lights: bpy_prop_collection[UserSolidLight]
    """ Lights used to display objects in solid shading mode

    :type: bpy_prop_collection[UserSolidLight]
    """

    texture_collection_rate: int
    """ Number of seconds between each run of the GL texture garbage collector

    :type: int
    """

    texture_time_out: int
    """ Time since last access of a GL texture in seconds after which it is freed (set to 0 to keep textures allocated)

    :type: int
    """

    ui_line_width: float
    """ Suggested line thickness and point size in pixels, for add-ons displaying custom user interface elements, based on operating system settings and Blender UI scale

    :type: float
    """

    ui_scale: float
    """ Size multiplier to use when displaying custom user interface elements, so that they are scaled correctly on screens with different DPI. This value is based on operating system DPI settings and Blender display scale

    :type: float
    """

    use_edit_mode_smooth_wire: bool
    """ Enable edit mode edge smoothing, reducing aliasing (requires restart)

    :type: bool
    """

    use_gpu_subdivision: bool
    """ Enable GPU acceleration for evaluating the last subdivision surface modifiers in the stack

    :type: bool
    """

    use_overlay_smooth_wire: bool
    """ Enable overlay smooth wires, reducing aliasing

    :type: bool
    """

    use_region_overlap: bool
    """ Display tool/property regions over the main region

    :type: bool
    """

    use_select_pick_depth: bool
    """ When making a selection in 3D View, use the GPU depth buffer to ensure the frontmost object is selected first

    :type: bool
    """

    use_sequencer_disk_cache: bool
    """ Store cached images to disk

    :type: bool
    """

    use_studio_light_edit: bool
    """ View the result of the studio light editor in the viewport

    :type: bool
    """

    vbo_collection_rate: int
    """ Number of seconds between each run of the GL vertex buffer object garbage collector

    :type: int
    """

    vbo_time_out: int
    """ Time since last access of a GL vertex buffer object in seconds after which it is freed (set to 0 to keep VBO allocated)

    :type: int
    """

    viewport_aa: str
    """ Method of anti-aliasing in 3d viewport

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
