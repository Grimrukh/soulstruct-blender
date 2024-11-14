import typing
import collections.abc
import mathutils
from .space import Space
from .struct import Struct
from .sequencer_timeline_overlay import SequencerTimelineOverlay
from .bpy_struct import bpy_struct
from .sequencer_preview_overlay import SequencerPreviewOverlay
from .grease_pencil import GreasePencil

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceSequenceEditor(Space, bpy_struct):
    """Sequence editor space data"""

    cursor_location: mathutils.Vector
    """ 2D cursor location for this view

    :type: mathutils.Vector
    """

    display_channel: int
    """ The channel number shown in the image preview. 0 is the result of all strips combined

    :type: int
    """

    display_mode: str
    """ View mode to use for displaying sequencer output

    :type: str
    """

    grease_pencil: GreasePencil
    """ Grease Pencil data for this Preview region

    :type: GreasePencil
    """

    overlay_frame_type: str
    """ Overlay display method

    :type: str
    """

    preview_channels: str
    """ Channels of the preview to display

    :type: str
    """

    preview_overlay: SequencerPreviewOverlay
    """ Settings for display of overlays

    :type: SequencerPreviewOverlay
    """

    proxy_render_size: str
    """ Display preview using full resolution or different proxy resolutions

    :type: str
    """

    show_backdrop: bool
    """ Display result under strips

    :type: bool
    """

    show_frames: bool
    """ Display frames rather than seconds

    :type: bool
    """

    show_gizmo: bool
    """ Show gizmos of all types

    :type: bool
    """

    show_gizmo_context: bool
    """ Context sensitive gizmos for the active item

    :type: bool
    """

    show_gizmo_navigate: bool
    """ Viewport navigation gizmo

    :type: bool
    """

    show_gizmo_tool: bool
    """ Active tool gizmo

    :type: bool
    """

    show_markers: bool
    """ If any exists, show markers in a separate row at the bottom of the editor

    :type: bool
    """

    show_overexposed: int
    """ Show overexposed areas with zebra stripes

    :type: int
    """

    show_overlays: bool
    """ 

    :type: bool
    """

    show_region_channels: bool
    """ 

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

    show_seconds: bool
    """ Show timing in seconds not frames

    :type: bool
    """

    show_separate_color: bool
    """ Separate color channels in preview

    :type: bool
    """

    show_transform_preview: bool
    """ Show preview of the transformed frames

    :type: bool
    """

    timeline_overlay: SequencerTimelineOverlay
    """ Settings for display of overlays

    :type: SequencerTimelineOverlay
    """

    use_clamp_view: bool
    """ Limit timeline height to maximum used channel slot

    :type: bool
    """

    use_marker_sync: bool
    """ Transform markers as well as strips

    :type: bool
    """

    use_proxies: bool
    """ Use optimized files for faster scrubbing when available

    :type: bool
    """

    use_zoom_to_fit: bool
    """ Automatically zoom preview image to make it fully fit the region

    :type: bool
    """

    view_type: str
    """ Type of the Sequencer view (sequencer, preview or both)

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
