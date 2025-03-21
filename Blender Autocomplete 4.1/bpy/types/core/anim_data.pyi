import typing
import collections.abc
import mathutils
from .action import Action
from .struct import Struct
from .bpy_struct import bpy_struct
from .anim_data_drivers import AnimDataDrivers
from .nla_tracks import NlaTracks

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AnimData(bpy_struct):
    """Animation data for data-block"""

    action: Action | None
    """ Active Action for this data-block

    :type: Action
    """

    action_blend_type: str
    """ Method used for combining Active Action's result with result of NLA stack

    :type: str
    """

    action_extrapolation: str
    """ Action to take for gaps past the Active Action's range (when evaluating with NLA)

    :type: str
    """

    action_influence: float
    """ Amount the Active Action contributes to the result of the NLA stack

    :type: float
    """

    action_tweak_storage: Action
    """ Slot to temporarily hold the main action while in tweak mode

    :type: Action
    """

    drivers: AnimDataDrivers
    """ The Drivers/Expressions for this data-block

    :type: AnimDataDrivers
    """

    nla_tracks: NlaTracks
    """ NLA Tracks (i.e. Animation Layers)

    :type: NlaTracks
    """

    use_nla: bool
    """ NLA stack is evaluated when evaluating this block

    :type: bool
    """

    use_pin: bool
    """ 

    :type: bool
    """

    use_tweak_mode: bool
    """ Whether to enable or disable tweak mode in NLA

    :type: bool
    """

    def nla_tweak_strip_time_to_scene(
        self, frame: float | None, invert: bool | typing.Any | None = False
    ) -> float:
        """Convert a time value from the local time of the tweaked strip to scene time, exactly as done by built-in key editing tools. Returns the input time unchanged if not tweaking.

        :param frame: Input time
        :type frame: float | None
        :param invert: Invert, Convert scene time to action time
        :type invert: bool | typing.Any | None
        :return: Converted time
        :rtype: float
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
