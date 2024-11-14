import typing
import collections.abc
import mathutils
from .image_user import ImageUser
from .struct import Struct
from .stereo3d_format import Stereo3dFormat
from .image_packed_file import ImagePackedFile
from .packed_file import PackedFile
from .scene import Scene
from .bpy_prop_collection import bpy_prop_collection
from .bpy_prop_array import bpy_prop_array
from .udim_tiles import UDIMTiles
from .color_managed_input_colorspace_settings import ColorManagedInputColorspaceSettings
from .render_slots import RenderSlots
from .bpy_struct import bpy_struct
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")

if typing.TYPE_CHECKING:
    from io_soulstruct import *


class Image(ID, bpy_struct):
    """Image data-block referencing an external or packed image"""

    # region Soulstruct Extensions
    DDS_TEXTURE: DDSTextureProps
    # endregion

    alpha_mode: str
    """ Representation of alpha in the image file, to convert to and from when saving and loading the image

    :type: str
    """

    bindcode: int
    """ OpenGL bindcode

    :type: int
    """

    channels: int
    """ Number of channels in pixels buffer

    :type: int
    """

    colorspace_settings: ColorManagedInputColorspaceSettings
    """ Input color space settings

    :type: ColorManagedInputColorspaceSettings
    """

    depth: int
    """ Image bit depth

    :type: int
    """

    display_aspect: mathutils.Vector
    """ Display Aspect for this image, does not affect rendering

    :type: mathutils.Vector
    """

    file_format: str
    """ Format used for re-saving this file

    :type: str
    """

    filepath: str
    """ Image/Movie file name

    :type: str
    """

    filepath_raw: str
    """ Image/Movie file name (without data refreshing)

    :type: str
    """

    frame_duration: int
    """ Duration (in frames) of the image (1 when not a video/sequence)

    :type: int
    """

    generated_color: bpy_prop_array[float]
    """ Fill color for the generated image

    :type: bpy_prop_array[float]
    """

    generated_height: int
    """ Generated image height

    :type: int
    """

    generated_type: str
    """ Generated image type

    :type: str
    """

    generated_width: int
    """ Generated image width

    :type: int
    """

    has_data: bool
    """ True if the image data is loaded into memory

    :type: bool
    """

    is_dirty: bool
    """ Image has changed and is not saved

    :type: bool
    """

    is_float: bool
    """ True if this image is stored in floating-point buffer

    :type: bool
    """

    is_multiview: bool
    """ Image has more than one view

    :type: bool
    """

    is_stereo_3d: bool
    """ Image has left and right views

    :type: bool
    """

    packed_file: PackedFile
    """ First packed file of the image

    :type: PackedFile
    """

    packed_files: bpy_prop_collection[ImagePackedFile]
    """ Collection of packed images

    :type: bpy_prop_collection[ImagePackedFile]
    """

    pixels: list[float]
    """ Image buffer pixels in floating-point values

    :type: float
    """

    render_slots: RenderSlots
    """ Render slots of the image

    :type: RenderSlots
    """

    resolution: mathutils.Vector
    """ X/Y pixels per meter, for the image buffer

    :type: mathutils.Vector
    """

    seam_margin: int
    """ Margin to take into account when fixing UV seams during painting. Higher number would improve seam-fixes for mipmaps, but decreases performance

    :type: int
    """

    size: bpy_prop_array[int]
    """ Width and height of the image buffer in pixels, zero when image data can't be loaded

    :type: bpy_prop_array[int]
    """

    source: str
    """ Where the image comes from

    :type: str
    """

    stereo_3d_format: Stereo3dFormat
    """ Settings for stereo 3d

    :type: Stereo3dFormat
    """

    tiles: UDIMTiles
    """ Tiles of the image

    :type: UDIMTiles
    """

    type: str
    """ How to generate the image

    :type: str
    """

    use_deinterlace: bool
    """ Deinterlace movie file on load

    :type: bool
    """

    use_generated_float: bool
    """ Generate floating-point buffer

    :type: bool
    """

    use_half_precision: bool
    """ Use 16 bits per channel to lower the memory usage during rendering

    :type: bool
    """

    use_multiview: bool
    """ Use Multiple Views (when available)

    :type: bool
    """

    use_view_as_render: bool
    """ Apply render part of display transformation when displaying this image on the screen

    :type: bool
    """

    views_format: str
    """ Mode to load image views

    :type: str
    """

    def save_render(
        self,
        filepath: str | typing.Any,
        scene: Scene | None = None,
        quality: typing.Any | None = 0,
    ):
        """Save image to a specific path using a scenes render settings

        :param filepath: Output path
        :type filepath: str | typing.Any
        :param scene: Scene to take image parameters from
        :type scene: Scene | None
        :param quality: Quality, Quality for image formats that support lossy compression, uses default quality if not specified
        :type quality: typing.Any | None
        """
        ...

    def save(self, filepath: str | typing.Any = "", quality: typing.Any | None = 0):
        """Save image

        :param filepath: Output path, uses image data-block filepath if not specified
        :type filepath: str | typing.Any
        :param quality: Quality, Quality for image formats that support lossy compression, uses default quality if not specified
        :type quality: typing.Any | None
        """
        ...

    def pack(self, data: str | typing.Any = "", data_len: typing.Any | None = 0):
        """Pack an image as embedded data into the .blend file

        :param data: data, Raw data (bytes, exact content of the embedded file)
        :type data: str | typing.Any
        :param data_len: data_len, length of given data (mandatory if data is provided)
        :type data_len: typing.Any | None
        """
        ...

    def unpack(self, method: str | None = "USE_LOCAL"):
        """Save an image packed in the .blend file to disk

        :param method: method, How to unpack
        :type method: str | None
        """
        ...

    def reload(self):
        """Reload the image from its source path"""
        ...

    def update(self):
        """Update the display image from the floating-point buffer"""
        ...

    def scale(
        self,
        width: int | None,
        height: int | None,
        frame: typing.Any | None = 0,
        tile_index: typing.Any | None = 0,
    ):
        """Scale the buffer of the image, in pixels

        :param width: Width
        :type width: int | None
        :param height: Height
        :type height: int | None
        :param frame: Frame, Frame (for image sequences)
        :type frame: typing.Any | None
        :param tile_index: Tile, Tile index (for tiled images)
        :type tile_index: typing.Any | None
        """
        ...

    def gl_touch(
        self,
        frame: typing.Any | None = 0,
        layer_index: typing.Any | None = 0,
        pass_index: typing.Any | None = 0,
    ) -> int:
        """Delay the image from being cleaned from the cache due inactivity

        :param frame: Frame, Frame of image sequence or movie
        :type frame: typing.Any | None
        :param layer_index: Layer, Index of layer that should be loaded
        :type layer_index: typing.Any | None
        :param pass_index: Pass, Index of pass that should be loaded
        :type pass_index: typing.Any | None
        :return: Error, OpenGL error value
        :rtype: int
        """
        ...

    def gl_load(
        self,
        frame: typing.Any | None = 0,
        layer_index: typing.Any | None = 0,
        pass_index: typing.Any | None = 0,
    ) -> int:
        """Load the image into an OpenGL texture. On success, image.bindcode will contain the OpenGL texture bindcode. Colors read from the texture will be in scene linear color space and have premultiplied or straight alpha matching the image alpha mode

        :param frame: Frame, Frame of image sequence or movie
        :type frame: typing.Any | None
        :param layer_index: Layer, Index of layer that should be loaded
        :type layer_index: typing.Any | None
        :param pass_index: Pass, Index of pass that should be loaded
        :type pass_index: typing.Any | None
        :return: Error, OpenGL error value
        :rtype: int
        """
        ...

    def gl_free(self):
        """Free the image from OpenGL graphics memory"""
        ...

    def filepath_from_user(
        self, image_user: ImageUser | None = None
    ) -> str | typing.Any:
        """Return the absolute path to the filepath of an image frame specified by the image user

        :param image_user: Image user of the image to get filepath for
        :type image_user: ImageUser | None
        :return: File Path, The resulting filepath from the image and its user
        :rtype: str | typing.Any
        """
        ...

    def buffers_free(self):
        """Free the image buffers from memory"""
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
