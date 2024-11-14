import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .boid_rule import BoidRule
from .bpy_struct import bpy_struct
from .boid_state import BoidState

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoidSettings(bpy_struct):
    """Settings for boid physics"""

    accuracy: float
    """ Accuracy of attack

    :type: float
    """

    active_boid_state: BoidRule
    """ 

    :type: BoidRule
    """

    active_boid_state_index: int | None
    """ 

    :type: int | None
    """

    aggression: float
    """ Boid will fight this times stronger enemy

    :type: float
    """

    air_acc_max: float
    """ Maximum acceleration in air (relative to maximum speed)

    :type: float
    """

    air_ave_max: float
    """ Maximum angular velocity in air (relative to 180 degrees)

    :type: float
    """

    air_personal_space: float
    """ Radius of boids personal space in air (% of particle size)

    :type: float
    """

    air_speed_max: float
    """ Maximum speed in air

    :type: float
    """

    air_speed_min: float
    """ Minimum speed in air (relative to maximum speed)

    :type: float
    """

    bank: float
    """ Amount of rotation around velocity vector on turns

    :type: float
    """

    health: float
    """ Initial boid health when born

    :type: float
    """

    height: float
    """ Boid height relative to particle size

    :type: float
    """

    land_acc_max: float
    """ Maximum acceleration on land (relative to maximum speed)

    :type: float
    """

    land_ave_max: float
    """ Maximum angular velocity on land (relative to 180 degrees)

    :type: float
    """

    land_jump_speed: float
    """ Maximum speed for jumping

    :type: float
    """

    land_personal_space: float
    """ Radius of boids personal space on land (% of particle size)

    :type: float
    """

    land_smooth: float
    """ How smoothly the boids land

    :type: float
    """

    land_speed_max: float
    """ Maximum speed on land

    :type: float
    """

    land_stick_force: float
    """ How strong a force must be to start effecting a boid on land

    :type: float
    """

    pitch: float
    """ Amount of rotation around side vector

    :type: float
    """

    range: float
    """ Maximum distance from which a boid can attack

    :type: float
    """

    states: bpy_prop_collection[BoidState]
    """ 

    :type: bpy_prop_collection[BoidState]
    """

    strength: float
    """ Maximum caused damage on attack per second

    :type: float
    """

    use_climb: bool
    """ Allow boids to climb goal objects

    :type: bool
    """

    use_flight: bool
    """ Allow boids to move in air

    :type: bool
    """

    use_land: bool
    """ Allow boids to move on land

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
