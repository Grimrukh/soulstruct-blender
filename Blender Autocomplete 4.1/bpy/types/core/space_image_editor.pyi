import typing
import collections.abc
import mathutils
from .space_uv_editor import SpaceUVEditor
from .image_user import ImageUser
from .mask import Mask
from .space import Space
from .struct import Struct
from .space_image_overlay import SpaceImageOverlay
from .bpy_prop_array import bpy_prop_array
from .image import Image
from .scopes import Scopes
from .histogram import Histogram
from .bpy_struct import bpy_struct
from .grease_pencil import GreasePencil

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceImageEditor(Space, bpy_struct):
    """Image and UV editor space data"""

    blend_factor: float
    """ Overlay blending factor of rasterized mask

    :type: float
    """

    cursor_location: mathutils.Vector
    """ 2D cursor location for this view

    :type: mathutils.Vector
    """

    display_channels: str
    """ Channels of the image to display

    :type: str
    """

    grease_pencil: GreasePencil
    """ Grease pencil data for this space

    :type: GreasePencil
    """

    image: Image
    """ Image displayed and edited in this space

    :type: Image
    """

    image_user: ImageUser
    """ Parameters defining which layer, pass and frame of the image is displayed

    :type: ImageUser
    """

    mask: Mask
    """ Mask displayed and edited in this space

    :type: Mask
    """

    mask_display_type: str
    """ Display type for mask splines

    :type: str
    """

    mask_overlay_mode: str
    """ Overlay mode of rasterized mask

    :type: str
    """

    mode: str
    """ Editing context being displayed

    :type: str
    """

    overlay: SpaceImageOverlay
    """ Settings for display of overlays in the UV/Image editor

    :type: SpaceImageOverlay
    """

    pivot_point: str
    """ Rotation/Scaling Pivot

    :type: str
    """

    sample_histogram: Histogram
    """ Sampled colors along line

    :type: Histogram
    """

    scopes: Scopes
    """ Scopes to visualize image statistics

    :type: Scopes
    """

    show_annotation: bool
    """ Show annotations for this view

    :type: bool
    """

    show_gizmo: bool
    """ Show gizmos of all types

    :type: bool
    """

    show_gizmo_navigate: bool
    """ Viewport navigation gizmo

    :type: bool
    """

    show_mask_overlay: bool
    """ 

    :type: bool
    """

    show_mask_spline: bool
    """ 

    :type: bool
    """

    show_maskedit: bool
    """ Show Mask editing related properties

    :type: bool
    """

    show_paint: bool
    """ Show paint related properties

    :type: bool
    """

    show_region_hud: bool
    """ 

    :type: bool
    """

    show_region_tool_header: bool
    """ 

    :type: bool
    """

    show_region_toolbar: bool
    """ 

    :type: bool
    """

    show_region_ui: bool
    """ 

    :type: bool
    """

    show_render: bool
    """ Show render related properties

    :type: bool
    """

    show_repeat: bool
    """ Display the image repeated outside of the main view

    :type: bool
    """

    show_stereo_3d: bool
    """ Display the image in Stereo 3D

    :type: bool
    """

    show_uvedit: bool
    """ Show UV editing related properties

    :type: bool
    """

    ui_mode: str
    """ Editing context being displayed

    :type: str
    """

    use_image_pin: bool
    """ Display current image regardless of object selection

    :type: bool
    """

    use_realtime_update: bool
    """ Update other affected window spaces automatically to reflect changes during interactive operations such as transform

    :type: bool
    """

    uv_editor: SpaceUVEditor
    """ UV editor settings

    :type: SpaceUVEditor
    """

    zoom: bpy_prop_array[float]
    """ Zoom factor

    :type: bpy_prop_array[float]
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

    @classmethod
    def draw_handler_add(
        cls,
        callback: typing.Any | None,
        args: tuple | None,
        region_type: str | None,
        draw_type: str | None,
    ) -> typing.Any:
        """Add a new draw handler to this space type.
        It will be called every time the specified region in the space type will be drawn.
        Note: All arguments are positional only for now.

                :param callback: A function that will be called when the region is drawn.
        It gets the specified arguments as input.
                :type callback: typing.Any | None
                :param args: Arguments that will be passed to the callback.
                :type args: tuple | None
                :param region_type: The region type the callback draws in; usually WINDOW. (`bpy.types.Region.type`)
                :type region_type: str | None
                :param draw_type: Usually POST_PIXEL for 2D drawing and POST_VIEW for 3D drawing. In some cases PRE_VIEW can be used. BACKDROP can be used for backdrops in the node editor.
                :type draw_type: str | None
                :return: Handler that can be removed later on.
                :rtype: typing.Any
        """
        ...

    @classmethod
    def draw_handler_remove(cls, handler: typing.Any | None, region_type: str | None):
        """Remove a draw handler that was added previously.

        :param handler: The draw handler that should be removed.
        :type handler: typing.Any | None
        :param region_type: Region type the callback was added to.
        :type region_type: str | None
        """
        ...
