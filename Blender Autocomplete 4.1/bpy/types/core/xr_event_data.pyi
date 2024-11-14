import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrEventData(bpy_struct):
    """XR Data for Window Manager Event"""

    action: str
    """ XR action name

    :type: str
    """

    action_set: str
    """ XR action set name

    :type: str
    """

    bimanual: bool
    """ Whether bimanual interaction is occurring

    :type: bool
    """

    controller_location: mathutils.Vector
    """ Location of the action's corresponding controller aim in world space

    :type: mathutils.Vector
    """

    controller_location_other: mathutils.Vector
    """ Controller aim location of the other user path for bimanual actions

    :type: mathutils.Vector
    """

    controller_rotation: mathutils.Quaternion
    """ Rotation of the action's corresponding controller aim in world space

    :type: mathutils.Quaternion
    """

    controller_rotation_other: mathutils.Quaternion
    """ Controller aim rotation of the other user path for bimanual actions

    :type: mathutils.Quaternion
    """

    float_threshold: float
    """ Input threshold for float/2D vector actions

    :type: float
    """

    state: bpy_prop_array[float]
    """ XR action values corresponding to type

    :type: bpy_prop_array[float]
    """

    state_other: bpy_prop_array[float]
    """ State of the other user path for bimanual actions

    :type: bpy_prop_array[float]
    """

    type: str
    """ XR action type

    :type: str
    """

    user_path: str
    """ User path of the action. E.g. "/user/hand/left"

    :type: str
    """

    user_path_other: str
    """ Other user path, for bimanual actions. E.g. "/user/hand/right"

    :type: str
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
