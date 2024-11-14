import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CollisionSettings(bpy_struct):
    """Collision settings for object in physics simulation"""

    absorption: float
    """ How much of effector force gets lost during collision with this object (in percent)

    :type: float
    """

    cloth_friction: float
    """ Friction for cloth collisions

    :type: float
    """

    damping: float
    """ Amount of damping during collision

    :type: float
    """

    damping_factor: float
    """ Amount of damping during particle collision

    :type: float
    """

    damping_random: float
    """ Random variation of damping

    :type: float
    """

    friction_factor: float
    """ Amount of friction during particle collision

    :type: float
    """

    friction_random: float
    """ Random variation of friction

    :type: float
    """

    permeability: float
    """ Chance that the particle will pass through the mesh

    :type: float
    """

    stickiness: float
    """ Amount of stickiness to surface collision

    :type: float
    """

    thickness_inner: float
    """ Inner face thickness (only used by softbodies)

    :type: float
    """

    thickness_outer: float
    """ Outer face thickness

    :type: float
    """

    use: bool
    """ Enable this object as a collider for physics systems

    :type: bool
    """

    use_culling: bool
    """ Cloth collision acts with respect to the collider normals (improves penetration recovery)

    :type: bool
    """

    use_normal: bool
    """ Cloth collision impulses act in the direction of the collider normals (more reliable in some cases)

    :type: bool
    """

    use_particle_kill: bool
    """ Kill collided particles

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
