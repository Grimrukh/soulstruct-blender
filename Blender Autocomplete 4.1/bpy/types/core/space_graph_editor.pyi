import typing
import collections.abc
import mathutils
from .space import Space
from .struct import Struct
from .bpy_struct import bpy_struct
from .dope_sheet import DopeSheet

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceGraphEditor(Space, bpy_struct):
    """Graph Editor space data"""

    autolock_translation_axis: bool
    """ Automatically locks the movement of keyframes to the dominant axis

    :type: bool
    """

    cursor_position_x: float
    """ Graph Editor 2D-Value cursor - X-Value component

    :type: float
    """

    cursor_position_y: float
    """ Graph Editor 2D-Value cursor - Y-Value component

    :type: float
    """

    dopesheet: DopeSheet
    """ Settings for filtering animation data

    :type: DopeSheet
    """

    has_ghost_curves: bool
    """ Graph Editor instance has some ghost curves stored

    :type: bool
    """

    mode: str
    """ Editing context being displayed

    :type: str
    """

    pivot_point: str
    """ Pivot center for rotation/scaling

    :type: str
    """

    show_cursor: bool
    """ Show 2D cursor

    :type: bool
    """

    show_extrapolation: bool
    """ 

    :type: bool
    """

    show_handles: bool
    """ Show handles of Bézier control points

    :type: bool
    """

    show_markers: bool
    """ If any exists, show markers in a separate row at the bottom of the editor

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

    show_region_ui: bool
    """ 

    :type: bool
    """

    show_seconds: bool
    """ Show timing in seconds not frames

    :type: bool
    """

    show_sliders: bool
    """ Show sliders beside F-Curve channels

    :type: bool
    """

    use_auto_merge_keyframes: bool
    """ Automatically merge nearby keyframes

    :type: bool
    """

    use_auto_normalization: bool
    """ Automatically recalculate curve normalization on every curve edit

    :type: bool
    """

    use_normalization: bool
    """ Display curves in normalized range from -1 to 1, for easier editing of multiple curves with different ranges

    :type: bool
    """

    use_only_selected_keyframe_handles: bool
    """ Only show and edit handles of selected keyframes

    :type: bool
    """

    use_realtime_update: bool
    """ When transforming keyframes, changes to the animation data are flushed to other views

    :type: bool
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
