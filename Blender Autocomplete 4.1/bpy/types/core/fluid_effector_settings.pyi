import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FluidEffectorSettings(bpy_struct):
    """Smoke collision settings"""

    effector_type: str
    """ Change type of effector in the simulation

    :type: str
    """

    guide_mode: str
    """ How to create guiding velocities

    :type: str
    """

    subframes: int
    """ Number of additional samples to take between frames to improve quality of fast moving effector objects

    :type: int
    """

    surface_distance: float
    """ Additional distance around mesh surface to consider as effector

    :type: float
    """

    use_effector: bool
    """ Control when to apply the effector

    :type: bool
    """

    use_plane_init: bool
    """ Treat this object as a planar, unclosed mesh

    :type: bool
    """

    velocity_factor: float
    """ Multiplier of obstacle velocity

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
