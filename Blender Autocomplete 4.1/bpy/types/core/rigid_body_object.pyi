import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RigidBodyObject(bpy_struct):
    """Settings for object participating in Rigid Body Simulation"""

    angular_damping: float
    """ Amount of angular velocity that is lost over time

    :type: float
    """

    collision_collections: list[bool]
    """ Collision collections rigid body belongs to

    :type: list[bool]
    """

    collision_margin: float
    """ Threshold of distance near surface where collisions are still considered (best results when non-zero)

    :type: float
    """

    collision_shape: str
    """ Collision Shape of object in Rigid Body Simulations

    :type: str
    """

    deactivate_angular_velocity: float
    """ Angular Velocity below which simulation stops simulating object

    :type: float
    """

    deactivate_linear_velocity: float
    """ Linear Velocity below which simulation stops simulating object

    :type: float
    """

    enabled: bool
    """ Rigid Body actively participates to the simulation

    :type: bool
    """

    friction: float
    """ Resistance of object to movement

    :type: float
    """

    kinematic: bool
    """ Allow rigid body to be controlled by the animation system

    :type: bool
    """

    linear_damping: float
    """ Amount of linear velocity that is lost over time

    :type: float
    """

    mass: float
    """ How much the object 'weighs' irrespective of gravity

    :type: float
    """

    mesh_source: str
    """ Source of the mesh used to create collision shape

    :type: str
    """

    restitution: float
    """ Tendency of object to bounce after colliding with another (0 = stays still, 1 = perfectly elastic)

    :type: float
    """

    type: str
    """ Role of object in Rigid Body Simulations

    :type: str
    """

    use_deactivation: bool
    """ Enable deactivation of resting rigid bodies (increases performance and stability but can cause glitches)

    :type: bool
    """

    use_deform: bool
    """ Rigid body deforms during simulation

    :type: bool
    """

    use_margin: bool
    """ Use custom collision margin (some shapes will have a visible gap around them)

    :type: bool
    """

    use_start_deactivated: bool
    """ Deactivate rigid body at the start of the simulation

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
