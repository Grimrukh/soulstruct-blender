import typing
import collections.abc
import mathutils
from .screen import Screen
from .stereo3d_display import Stereo3dDisplay
from .struct import Struct
from .bpy_struct import bpy_struct
from .work_space import WorkSpace
from .view_layer import ViewLayer
from .event import Event
from .scene import Scene

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Window(bpy_struct):
    """Open window"""

    height: int
    """ Window height

    :type: int
    """

    parent: Window
    """ Active workspace and scene follow this window

    :type: Window
    """

    scene: Scene
    """ Active scene to be edited in the window

    :type: Scene
    """

    screen: Screen
    """ Active workspace screen showing in the window

    :type: Screen
    """

    stereo_3d_display: Stereo3dDisplay
    """ Settings for stereo 3D display

    :type: Stereo3dDisplay
    """

    view_layer: ViewLayer
    """ The active workspace view layer showing in the window

    :type: ViewLayer
    """

    width: int
    """ Window width

    :type: int
    """

    workspace: WorkSpace
    """ Active workspace showing in the window

    :type: WorkSpace
    """

    x: int
    """ Horizontal location of the window

    :type: int
    """

    y: int
    """ Vertical location of the window

    :type: int
    """

    def cursor_warp(self, x: int | None, y: int | None):
        """Set the cursor position

        :param x:
        :type x: int | None
        :param y:
        :type y: int | None
        """
        ...

    def cursor_set(self, cursor: str | None):
        """Set the cursor

        :param cursor: cursor
        :type cursor: str | None
        """
        ...

    def cursor_modal_set(self, cursor: str | None):
        """Restore the previous cursor after calling cursor_modal_set

        :param cursor: cursor
        :type cursor: str | None
        """
        ...

    def cursor_modal_restore(self):
        """cursor_modal_restore"""
        ...

    def event_simulate(
        self,
        type: str | None,
        value: str | None,
        unicode: str | typing.Any | None = "",
        x: typing.Any | None = 0,
        y: typing.Any | None = 0,
        shift: bool | typing.Any | None = False,
        ctrl: bool | typing.Any | None = False,
        alt: bool | typing.Any | None = False,
        oskey: bool | typing.Any | None = False,
    ) -> Event:
        """event_simulate

        :param type: Type
        :type type: str | None
        :param value: Value
        :type value: str | None
        :param unicode:
        :type unicode: str | typing.Any | None
        :param x:
        :type x: typing.Any | None
        :param y:
        :type y: typing.Any | None
        :param shift: Shift
        :type shift: bool | typing.Any | None
        :param ctrl: Ctrl
        :type ctrl: bool | typing.Any | None
        :param alt: Alt
        :type alt: bool | typing.Any | None
        :param oskey: OS Key
        :type oskey: bool | typing.Any | None
        :return: Item, Added key map item
        :rtype: Event
        """
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
