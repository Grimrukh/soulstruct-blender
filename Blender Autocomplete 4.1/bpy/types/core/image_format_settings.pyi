import typing
import collections.abc
import mathutils
from .color_managed_input_colorspace_settings import ColorManagedInputColorspaceSettings
from .stereo3d_format import Stereo3dFormat
from .struct import Struct
from .color_managed_display_settings import ColorManagedDisplaySettings
from .bpy_struct import bpy_struct
from .color_managed_view_settings import ColorManagedViewSettings

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ImageFormatSettings(bpy_struct):
    """Settings for image formats"""

    cineon_black: int
    """ Log conversion reference blackpoint

    :type: int
    """

    cineon_gamma: float
    """ Log conversion gamma

    :type: float
    """

    cineon_white: int
    """ Log conversion reference whitepoint

    :type: int
    """

    color_depth: str
    """ Bit depth per channel

    :type: str
    """

    color_management: str
    """ Which color management settings to use for file saving

    :type: str
    """

    color_mode: str
    """ Choose BW for saving grayscale images, RGB for saving red, green and blue channels, and RGBA for saving red, green, blue and alpha channels

    :type: str
    """

    compression: int
    """ Amount of time to determine best compression: 0 = no compression with fast file output, 100 = maximum lossless compression with slow file output

    :type: int
    """

    display_settings: ColorManagedDisplaySettings
    """ Settings of device saved image would be displayed on

    :type: ColorManagedDisplaySettings
    """

    exr_codec: str
    """ Codec settings for OpenEXR

    :type: str
    """

    file_format: str
    """ File format to save the rendered images as

    :type: str
    """

    has_linear_colorspace: bool
    """ File format expects linear color space

    :type: bool
    """

    jpeg2k_codec: str
    """ Codec settings for JPEG 2000

    :type: str
    """

    linear_colorspace_settings: ColorManagedInputColorspaceSettings
    """ Output color space settings

    :type: ColorManagedInputColorspaceSettings
    """

    quality: int
    """ Quality for image formats that support lossy compression

    :type: int
    """

    stereo_3d_format: Stereo3dFormat
    """ Settings for stereo 3D

    :type: Stereo3dFormat
    """

    tiff_codec: str
    """ Compression mode for TIFF

    :type: str
    """

    use_cineon_log: bool
    """ Convert to logarithmic color space

    :type: bool
    """

    use_jpeg2k_cinema_48: bool
    """ Use OpenJPEG Cinema Preset (48fps)

    :type: bool
    """

    use_jpeg2k_cinema_preset: bool
    """ Use OpenJPEG Cinema Preset

    :type: bool
    """

    use_jpeg2k_ycc: bool
    """ Save luminance-chrominance-chrominance channels instead of RGB colors

    :type: bool
    """

    use_preview: bool
    """ When rendering animations, save JPG preview images in same directory

    :type: bool
    """

    view_settings: ColorManagedViewSettings
    """ Color management settings applied on image before saving

    :type: ColorManagedViewSettings
    """

    views_format: str
    """ Format of multiview media

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
