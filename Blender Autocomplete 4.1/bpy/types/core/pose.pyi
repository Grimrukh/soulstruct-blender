import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .action import Action
from .anim_viz import AnimViz
from .struct import Struct
from .bpy_struct import bpy_struct
from .pose_bone import PoseBone
from .ik_param import IKParam

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Pose(bpy_struct):
    """A collection of pose channels, including settings for animating bones"""

    animation_visualization: AnimViz
    """ Animation data for this data-block

    :type: AnimViz
    """

    bones: bpy_prop_collection[PoseBone]
    """ Individual pose bones for the armature

    :type: bpy_prop_collection[PoseBone]
    """

    ik_param: IKParam
    """ Parameters for IK solver

    :type: IKParam
    """

    ik_solver: str
    """ Selection of IK solver for IK chain

    :type: str
    """

    use_auto_ik: bool
    """ Add temporary IK constraints while grabbing bones in Pose Mode

    :type: bool
    """

    use_mirror_relative: bool
    """ Apply relative transformations in X-mirror mode (not supported with Auto IK)

    :type: bool
    """

    use_mirror_x: bool
    """ Apply changes to matching bone on opposite side of X-Axis

    :type: bool
    """

    @classmethod
    def apply_pose_from_action(
        cls, action: Action | None, evaluation_time: typing.Any | None = 0.0
    ):
        """Apply the given action to this pose by evaluating it at a specific time. Only updates the pose of selected bones, or all bones if none are selected.

        :param action: Action, The Action containing the pose
        :type action: Action | None
        :param evaluation_time: Evaluation Time, Time at which the given action is evaluated to obtain the pose
        :type evaluation_time: typing.Any | None
        """
        ...

    @classmethod
    def blend_pose_from_action(
        cls,
        action: Action | None,
        blend_factor: typing.Any | None = 1.0,
        evaluation_time: typing.Any | None = 0.0,
    ):
        """Blend the given action into this pose by evaluating it at a specific time. Only updates the pose of selected bones, or all bones if none are selected.

        :param action: Action, The Action containing the pose
        :type action: Action | None
        :param blend_factor: Blend Factor, How much the given Action affects the final pose
        :type blend_factor: typing.Any | None
        :param evaluation_time: Evaluation Time, Time at which the given action is evaluated to obtain the pose
        :type evaluation_time: typing.Any | None
        """
        ...

    @classmethod
    def backup_create(cls, action: Action | None):
        """Create a backup of the current pose. Only those bones that are animated in the Action are backed up. The object owns the backup, and each object can have only one backup at a time. When you no longer need it, it must be freed use backup_clear()

        :param action: Action, An Action with animation data for the bones. Only the animated bones will be included in the backup
        :type action: Action | None
        """
        ...

    @classmethod
    def backup_restore(cls) -> bool:
        """Restore the previously made pose backup. This can be called multiple times. See Pose.backup_create() for more info

        :return: True when the backup was restored, False if there was no backup to restore
        :rtype: bool
        """
        ...

    @classmethod
    def backup_clear(cls):
        """Free a previously made pose backup. See Pose.backup_create() for more info."""
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
