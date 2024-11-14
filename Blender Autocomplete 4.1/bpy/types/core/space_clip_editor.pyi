import typing
import collections.abc
import mathutils
from .mask import Mask
from .space import Space
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_clip_scopes import MovieClipScopes
from .movie_clip_user import MovieClipUser
from .movie_clip import MovieClip

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceClipEditor(Space, bpy_struct):
    """Clip editor space data"""

    annotation_source: str
    """ Where the annotation comes from

    :type: str
    """

    blend_factor: float
    """ Overlay blending factor of rasterized mask

    :type: float
    """

    clip: MovieClip
    """ Movie clip displayed and edited in this space

    :type: MovieClip
    """

    clip_user: MovieClipUser
    """ Parameters defining which frame of the movie clip is displayed

    :type: MovieClipUser
    """

    cursor_location: mathutils.Vector
    """ 2D cursor location for this view

    :type: mathutils.Vector
    """

    lock_selection: bool
    """ Lock viewport to selected markers during playback

    :type: bool
    """

    lock_time_cursor: bool
    """ Lock curves view to time cursor during playback and tracking

    :type: bool
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

    path_length: int
    """ Length of displaying path, in frames

    :type: int
    """

    pivot_point: str
    """ Pivot center for rotation/scaling

    :type: str
    """

    scopes: MovieClipScopes
    """ Scopes to visualize movie clip statistics

    :type: MovieClipScopes
    """

    show_annotation: bool
    """ Show annotations for this view

    :type: bool
    """

    show_blue_channel: bool
    """ Show blue channel in the frame

    :type: bool
    """

    show_bundles: bool
    """ Show projection of 3D markers into footage

    :type: bool
    """

    show_disabled: bool
    """ Show disabled tracks from the footage

    :type: bool
    """

    show_filters: bool
    """ Show filters for graph editor

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

    show_graph_frames: bool
    """ Show curve for per-frame average error (camera motion should be solved first)

    :type: bool
    """

    show_graph_hidden: bool
    """ Include channels from objects/bone that are not visible

    :type: bool
    """

    show_graph_only_selected: bool
    """ Only include channels relating to selected objects and data

    :type: bool
    """

    show_graph_tracks_error: bool
    """ Display the reprojection error curve for selected tracks

    :type: bool
    """

    show_graph_tracks_motion: bool
    """ Display the speed curves (in "x" direction red, in "y" direction green) for the selected tracks

    :type: bool
    """

    show_green_channel: bool
    """ Show green channel in the frame

    :type: bool
    """

    show_grid: bool
    """ Show grid showing lens distortion

    :type: bool
    """

    show_marker_pattern: bool
    """ Show pattern boundbox for markers

    :type: bool
    """

    show_marker_search: bool
    """ Show search boundbox for markers

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

    show_metadata: bool
    """ Show metadata of clip

    :type: bool
    """

    show_names: bool
    """ Show track names and status

    :type: bool
    """

    show_red_channel: bool
    """ Show red channel in the frame

    :type: bool
    """

    show_region_hud: bool
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

    show_stable: bool
    """ Show stable footage in editor (if stabilization is enabled)

    :type: bool
    """

    show_tiny_markers: bool
    """ Show markers in a more compact manner

    :type: bool
    """

    show_track_path: bool
    """ Show path of how track moves

    :type: bool
    """

    use_grayscale_preview: bool
    """ Display frame in grayscale mode

    :type: bool
    """

    use_manual_calibration: bool
    """ Use manual calibration helpers

    :type: bool
    """

    use_mute_footage: bool
    """ Mute footage and show black background instead

    :type: bool
    """

    view: str
    """ Type of the clip editor view

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
