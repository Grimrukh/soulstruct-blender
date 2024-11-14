import typing
import collections.abc
import mathutils
from .space import Space
from .action import Action
from .struct import Struct
from .bpy_struct import bpy_struct
from .dope_sheet import DopeSheet

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceDopeSheetEditor(Space, bpy_struct):
    """Dope Sheet space data"""

    action: Action
    """ Action displayed and edited in this space

    :type: Action
    """

    cache_cloth: bool
    """ Show the active object's cloth point cache

    :type: bool
    """

    cache_dynamicpaint: bool
    """ Show the active object's Dynamic Paint cache

    :type: bool
    """

    cache_particles: bool
    """ Show the active object's particle point cache

    :type: bool
    """

    cache_rigidbody: bool
    """ Show the active object's Rigid Body cache

    :type: bool
    """

    cache_simulation_nodes: bool
    """ Show the active object's simulation nodes cache and bake data

    :type: bool
    """

    cache_smoke: bool
    """ Show the active object's smoke cache

    :type: bool
    """

    cache_softbody: bool
    """ Show the active object's softbody point cache

    :type: bool
    """

    dopesheet: DopeSheet
    """ Settings for filtering animation data

    :type: DopeSheet
    """

    mode: str
    """ Editing context being displayed

    :type: str
    """

    show_cache: bool
    """ Show the status of cached frames in the timeline

    :type: bool
    """

    show_extremes: bool
    """ Mark keyframes where the key value flow changes direction, based on comparison with adjacent keys

    :type: bool
    """

    show_interpolation: bool
    """ Display keyframe handle types and non-Bézier interpolation modes

    :type: bool
    """

    show_markers: bool
    """ If any exists, show markers in a separate row at the bottom of the editor

    :type: bool
    """

    show_pose_markers: bool
    """ Show markers belonging to the active action instead of Scene markers (Action and Shape Key Editors only)

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

    ui_mode: str
    """ Editing context being displayed

    :type: str
    """

    use_auto_merge_keyframes: bool
    """ Automatically merge nearby keyframes

    :type: bool
    """

    use_marker_sync: bool
    """ Sync Markers with keyframe edits

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
