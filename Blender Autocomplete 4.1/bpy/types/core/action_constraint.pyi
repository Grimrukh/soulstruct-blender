import typing
import collections.abc
import mathutils
from .action import Action
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ActionConstraint(Constraint, bpy_struct):
    """Map an action to the transform axes of a bone"""

    action: Action
    """ The constraining action

    :type: Action
    """

    eval_time: float
    """ Interpolates between Action Start and End frames

    :type: float
    """

    frame_end: int
    """ Last frame of the Action to use

    :type: int
    """

    frame_start: int
    """ First frame of the Action to use

    :type: int
    """

    max: float
    """ Maximum value for target channel range

    :type: float
    """

    min: float
    """ Minimum value for target channel range

    :type: float
    """

    mix_mode: str
    """ Specify how existing transformations and the action channels are combined

    :type: str
    """

    subtarget: str
    """ Armature bone, mesh or lattice vertex group, ...

    :type: str
    """

    target: Object
    """ Target object

    :type: Object
    """

    transform_channel: str
    """ Transformation channel from the target that is used to key the Action

    :type: str
    """

    use_bone_object_action: bool
    """ Bones only: apply the object's transformation channels of the action to the constrained bone, instead of bone's channels

    :type: bool
    """

    use_eval_time: bool
    """ Interpolate between Action Start and End frames, with the Evaluation Time slider instead of the Target object/bone

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
