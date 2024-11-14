import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CameraStereoData(bpy_struct):
    """Stereoscopy settings for a Camera data-block"""

    convergence_distance: float
    """ The converge point for the stereo cameras (often the distance between a projector and the projection screen)

    :type: float
    """

    convergence_mode: str
    """ 

    :type: str
    """

    interocular_distance: float
    """ Set the distance between the eyes - the stereo plane distance / 30 should be fine

    :type: float
    """

    pivot: str
    """ 

    :type: str
    """

    pole_merge_angle_from: float
    """ Angle at which interocular distance starts to fade to 0

    :type: float
    """

    pole_merge_angle_to: float
    """ Angle at which interocular distance is 0

    :type: float
    """

    use_pole_merge: bool
    """ Fade interocular distance to 0 after the given cutoff angle

    :type: bool
    """

    use_spherical_stereo: bool
    """ Render every pixel rotating the camera around the middle of the interocular distance

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
