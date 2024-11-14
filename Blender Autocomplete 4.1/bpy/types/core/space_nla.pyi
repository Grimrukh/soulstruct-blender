import typing
import collections.abc
import mathutils
from .space import Space
from .struct import Struct
from .bpy_struct import bpy_struct
from .dope_sheet import DopeSheet

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceNLA(Space, bpy_struct):
    """NLA editor space data"""

    dopesheet: DopeSheet
    """ Settings for filtering animation data

    :type: DopeSheet
    """

    show_local_markers: bool
    """ Show action-local markers on the strips, useful when synchronizing timing across strips

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

    show_strip_curves: bool
    """ Show influence F-Curves on strips

    :type: bool
    """

    use_realtime_update: bool
    """ When transforming strips, changes to the animation data are flushed to other views

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
