import typing
import collections.abc
import mathutils
from .xr_component_paths import XrComponentPaths
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrActionMapBinding(bpy_struct):
    """Binding in an XR action map item"""

    axis0_region: str
    """ Action execution region for the first input axis

    :type: str
    """

    axis1_region: str
    """ Action execution region for the second input axis

    :type: str
    """

    component_paths: XrComponentPaths
    """ OpenXR component paths

    :type: XrComponentPaths
    """

    name: str
    """ Name of the action map binding

    :type: str
    """

    pose_location: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    pose_rotation: mathutils.Euler
    """ 

    :type: mathutils.Euler
    """

    profile: str
    """ OpenXR interaction profile path

    :type: str
    """

    threshold: float
    """ Input threshold for button/axis actions

    :type: float
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
