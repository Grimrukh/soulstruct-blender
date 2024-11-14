import typing
import collections.abc
import mathutils
from .xr_action_map_binding import XrActionMapBinding
from .xr_action_map_item import XrActionMapItem
from .struct import Struct
from .xr_action_map import XrActionMap
from .bpy_struct import bpy_struct
from .xr_action_maps import XrActionMaps
from .context import Context

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrSessionState(bpy_struct):
    """Runtime state information about the VR session"""

    actionmaps: XrActionMaps
    """ 

    :type: XrActionMaps
    """

    active_actionmap: int | None
    """ 

    :type: int | None
    """

    navigation_location: mathutils.Vector
    """ Location offset to apply to base pose when determining viewer location

    :type: mathutils.Vector
    """

    navigation_rotation: mathutils.Quaternion
    """ Rotation offset to apply to base pose when determining viewer rotation

    :type: mathutils.Quaternion
    """

    navigation_scale: float
    """ Additional scale multiplier to apply to base scale when determining viewer scale

    :type: float
    """

    selected_actionmap: int
    """ 

    :type: int
    """

    viewer_pose_location: mathutils.Vector
    """ Last known location of the viewer pose (center between the eyes) in world space

    :type: mathutils.Vector
    """

    viewer_pose_rotation: mathutils.Quaternion
    """ Last known rotation of the viewer pose (center between the eyes) in world space

    :type: mathutils.Quaternion
    """

    @classmethod
    def is_running(cls, context: Context) -> bool:
        """Query if the VR session is currently running

        :param context:
        :type context: Context
        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def reset_to_base_pose(cls, context: Context):
        """Force resetting of position and rotation deltas

        :param context:
        :type context: Context
        """
        ...

    @classmethod
    def action_set_create(cls, context: Context, actionmap: XrActionMap) -> bool:
        """Create a VR action set

        :param context:
        :type context: Context
        :param actionmap:
        :type actionmap: XrActionMap
        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def action_create(
        cls, context: Context, actionmap: XrActionMap, actionmap_item: XrActionMapItem
    ) -> bool:
        """Create a VR action

        :param context:
        :type context: Context
        :param actionmap:
        :type actionmap: XrActionMap
        :param actionmap_item:
        :type actionmap_item: XrActionMapItem
        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def action_binding_create(
        cls,
        context: Context,
        actionmap: XrActionMap,
        actionmap_item: XrActionMapItem,
        actionmap_binding: XrActionMapBinding,
    ) -> bool:
        """Create a VR action binding

        :param context:
        :type context: Context
        :param actionmap:
        :type actionmap: XrActionMap
        :param actionmap_item:
        :type actionmap_item: XrActionMapItem
        :param actionmap_binding:
        :type actionmap_binding: XrActionMapBinding
        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def active_action_set_set(
        cls, context: Context, action_set: str | typing.Any
    ) -> bool:
        """Set the active VR action set

        :param context:
        :type context: Context
        :param action_set: Action Set, Action set name
        :type action_set: str | typing.Any
        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def controller_pose_actions_set(
        cls,
        context: Context,
        action_set: str | typing.Any,
        grip_action: str | typing.Any,
        aim_action: str | typing.Any,
    ) -> bool:
        """Set the actions that determine the VR controller poses

        :param context:
        :type context: Context
        :param action_set: Action Set, Action set name
        :type action_set: str | typing.Any
        :param grip_action: Grip Action, Name of the action representing the controller grips
        :type grip_action: str | typing.Any
        :param aim_action: Aim Action, Name of the action representing the controller aims
        :type aim_action: str | typing.Any
        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def action_state_get(
        cls,
        context: Context,
        action_set_name: str | typing.Any,
        action_name: str | typing.Any,
        user_path: str | typing.Any,
    ) -> typing.Any:
        """Get the current state of a VR action

        :param context:
        :type context: Context
        :param action_set_name: Action Set, Action set name
        :type action_set_name: str | typing.Any
        :param action_name: Action, Action name
        :type action_name: str | typing.Any
        :param user_path: User Path, OpenXR user path
        :type user_path: str | typing.Any
        :return: Action State, Current state of the VR action. Second float value is only set for 2D vector type actions
        :rtype: typing.Any
        """
        ...

    @classmethod
    def haptic_action_apply(
        cls,
        context: Context,
        action_set_name: str | typing.Any,
        action_name: str | typing.Any,
        user_path: str | typing.Any,
        duration: float | None,
        frequency: float | None,
        amplitude: float | None,
    ) -> bool:
        """Apply a VR haptic action

        :param context:
        :type context: Context
        :param action_set_name: Action Set, Action set name
        :type action_set_name: str | typing.Any
        :param action_name: Action, Action name
        :type action_name: str | typing.Any
        :param user_path: User Path, Optional OpenXR user path. If not set, the action will be applied to all paths
        :type user_path: str | typing.Any
        :param duration: Duration, Haptic duration in seconds. 0.0 is the minimum supported duration
        :type duration: float | None
        :param frequency: Frequency, Frequency of the haptic vibration in hertz. 0.0 specifies the OpenXR runtime's default frequency
        :type frequency: float | None
        :param amplitude: Amplitude, Haptic amplitude, ranging from 0.0 to 1.0
        :type amplitude: float | None
        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def haptic_action_stop(
        cls,
        context: Context,
        action_set_name: str | typing.Any,
        action_name: str | typing.Any,
        user_path: str | typing.Any,
    ):
        """Stop a VR haptic action

        :param context:
        :type context: Context
        :param action_set_name: Action Set, Action set name
        :type action_set_name: str | typing.Any
        :param action_name: Action, Action name
        :type action_name: str | typing.Any
        :param user_path: User Path, Optional OpenXR user path. If not set, the action will be stopped for all paths
        :type user_path: str | typing.Any
        """
        ...

    @classmethod
    def controller_grip_location_get(
        cls, context: Context, index: int | None
    ) -> typing.Any:
        """Get the last known controller grip location in world space

        :param context:
        :type context: Context
        :param index: Index, Controller index
        :type index: int | None
        :return: Location, Controller grip location
        :rtype: typing.Any
        """
        ...

    @classmethod
    def controller_grip_rotation_get(
        cls, context: Context, index: int | None
    ) -> typing.Any:
        """Get the last known controller grip rotation (quaternion) in world space

        :param context:
        :type context: Context
        :param index: Index, Controller index
        :type index: int | None
        :return: Rotation, Controller grip quaternion rotation
        :rtype: typing.Any
        """
        ...

    @classmethod
    def controller_aim_location_get(
        cls, context: Context, index: int | None
    ) -> typing.Any:
        """Get the last known controller aim location in world space

        :param context:
        :type context: Context
        :param index: Index, Controller index
        :type index: int | None
        :return: Location, Controller aim location
        :rtype: typing.Any
        """
        ...

    @classmethod
    def controller_aim_rotation_get(
        cls, context: Context, index: int | None
    ) -> typing.Any:
        """Get the last known controller aim rotation (quaternion) in world space

        :param context:
        :type context: Context
        :param index: Index, Controller index
        :type index: int | None
        :return: Rotation, Controller aim quaternion rotation
        :rtype: typing.Any
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
