import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .xr_action_map_bindings import XrActionMapBindings
from .operator_properties import OperatorProperties
from .xr_user_paths import XrUserPaths

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrActionMapItem(bpy_struct):
    bimanual: bool
    """ The action depends on the states/poses of both user paths

    :type: bool
    """

    bindings: XrActionMapBindings
    """ Bindings for the action map item, mapping the action to an XR input

    :type: XrActionMapBindings
    """

    haptic_amplitude: float
    """ Intensity of the haptic vibration, ranging from 0.0 to 1.0

    :type: float
    """

    haptic_duration: float
    """ Haptic duration in seconds. 0.0 is the minimum supported duration

    :type: float
    """

    haptic_frequency: float
    """ Frequency of the haptic vibration in hertz. 0.0 specifies the OpenXR runtime's default frequency

    :type: float
    """

    haptic_match_user_paths: bool
    """ Apply haptics to the same user paths for the haptic action and this action

    :type: bool
    """

    haptic_mode: str
    """ Haptic application mode

    :type: str
    """

    haptic_name: str
    """ Name of the haptic action to apply when executing this action

    :type: str
    """

    name: str
    """ Name of the action map item

    :type: str
    """

    op: str
    """ Identifier of operator to call on action event

    :type: str
    """

    op_mode: str
    """ Operator execution mode

    :type: str
    """

    op_name: str
    """ Name of operator (translated) to call on action event

    :type: str
    """

    op_properties: OperatorProperties
    """ Properties to set when the operator is called

    :type: OperatorProperties
    """

    pose_is_controller_aim: bool
    """ The action poses will be used for the VR controller aims

    :type: bool
    """

    pose_is_controller_grip: bool
    """ The action poses will be used for the VR controller grips

    :type: bool
    """

    selected_binding: int
    """ Currently selected binding

    :type: int
    """

    type: str
    """ Action type

    :type: str
    """

    user_paths: XrUserPaths
    """ OpenXR user paths

    :type: XrUserPaths
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
