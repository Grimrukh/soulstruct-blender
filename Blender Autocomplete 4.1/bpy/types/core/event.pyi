import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .xr_event_data import XrEventData

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Event(bpy_struct):
    """Window Manager Event"""

    alt: bool
    """ True when the Alt/Option key is held

    :type: bool
    """

    ascii: str
    """ Single ASCII character for this event

    :type: str
    """

    ctrl: bool
    """ True when the Ctrl key is held

    :type: bool
    """

    direction: str
    """ The direction (only applies to drag events)

    :type: str
    """

    is_consecutive: bool
    """ Part of a trackpad or NDOF motion, interrupted by cursor motion, button or key press events

    :type: bool
    """

    is_mouse_absolute: bool
    """ The last motion event was an absolute input

    :type: bool
    """

    is_repeat: bool
    """ The event is generated by holding a key down

    :type: bool
    """

    is_tablet: bool
    """ The event has tablet data

    :type: bool
    """

    mouse_prev_press_x: int
    """ The window relative horizontal location of the last press event

    :type: int
    """

    mouse_prev_press_y: int
    """ The window relative vertical location of the last press event

    :type: int
    """

    mouse_prev_x: int
    """ The window relative horizontal location of the mouse

    :type: int
    """

    mouse_prev_y: int
    """ The window relative vertical location of the mouse

    :type: int
    """

    mouse_region_x: int
    """ The region relative horizontal location of the mouse

    :type: int
    """

    mouse_region_y: int
    """ The region relative vertical location of the mouse

    :type: int
    """

    mouse_x: int
    """ The window relative horizontal location of the mouse

    :type: int
    """

    mouse_y: int
    """ The window relative vertical location of the mouse

    :type: int
    """

    oskey: bool
    """ True when the Cmd key is held

    :type: bool
    """

    pressure: float
    """ The pressure of the tablet or 1.0 if no tablet present

    :type: float
    """

    shift: bool
    """ True when the Shift key is held

    :type: bool
    """

    tilt: mathutils.Vector
    """ The pressure of the tablet or zeroes if no tablet present

    :type: mathutils.Vector
    """

    type: str
    """ 

    :type: str
    """

    type_prev: str
    """ 

    :type: str
    """

    unicode: str
    """ Single unicode character for this event

    :type: str
    """

    value: str
    """ The type of event, only applies to some

    :type: str
    """

    value_prev: str
    """ The type of event, only applies to some

    :type: str
    """

    xr: XrEventData
    """ XR event data

    :type: XrEventData
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