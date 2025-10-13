import typing
import collections.abc
import mathutils
from .struct import Struct
from .action_f_curves import ActionFCurves
from .bpy_struct import bpy_struct
from .action_groups import ActionGroups
from .id import ID
from .object import Object
from .action_pose_markers import ActionPoseMarkers

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Action(ID, bpy_struct):
    """A collection of F-Curves for animation"""

    curve_frame_range: mathutils.Vector
    """ The combined frame range of all F-Curves within this action

    :type: mathutils.Vector
    """

    fcurves: ActionFCurves
    """ The individual F-Curves that make up the action

    :type: ActionFCurves
    """

    frame_end: float
    """ The end frame of the manually set intended playback range

    :type: float
    """

    frame_range: mathutils.Vector
    """ The intended playback frame range of this action, using the manually set range if available, or the combined frame range of all F-Curves within this action if not (assigning sets the manual frame range)

    :type: mathutils.Vector
    """

    frame_start: float
    """ The start frame of the manually set intended playback range

    :type: float
    """

    groups: ActionGroups
    """ Convenient groupings of F-Curves

    :type: ActionGroups
    """

    id_root: str
    """ Type of ID block that action can be used on - DO NOT CHANGE UNLESS YOU KNOW WHAT YOU ARE DOING

    :type: str
    """

    pose_markers: ActionPoseMarkers
    """ Markers specific to this action, for labeling poses

    :type: ActionPoseMarkers
    """

    slots: typing.Any
    """ Action slots (Blender 4.4 and later) """

    use_cyclic: bool
    """ The action is intended to be used as a cycle looping over its manually set playback frame range (enabling this doesn't automatically make it loop)

    :type: bool
    """

    use_frame_range: bool
    """ Manually specify the intended playback frame range for the action (this range is used by some tools, but does not affect animation evaluation)

    :type: bool
    """

    def flip_with_pose(self, object: Object):
        """Flip the action around the X axis using a pose

        :param object: The reference armature object to use when flipping
        :type object: Object
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
