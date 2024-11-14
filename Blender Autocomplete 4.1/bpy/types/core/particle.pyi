import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .particle_system_modifier import ParticleSystemModifier
from .struct import Struct
from .bpy_struct import bpy_struct
from .particle_hair_key import ParticleHairKey
from .particle_key import ParticleKey

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Particle(bpy_struct):
    """Particle in a particle system"""

    alive_state: str
    """ 

    :type: str
    """

    angular_velocity: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    birth_time: float
    """ 

    :type: float
    """

    die_time: float
    """ 

    :type: float
    """

    hair_keys: bpy_prop_collection[ParticleHairKey]
    """ 

    :type: bpy_prop_collection[ParticleHairKey]
    """

    is_exist: bool
    """ 

    :type: bool
    """

    is_visible: bool
    """ 

    :type: bool
    """

    lifetime: float
    """ 

    :type: float
    """

    location: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    particle_keys: bpy_prop_collection[ParticleKey]
    """ 

    :type: bpy_prop_collection[ParticleKey]
    """

    prev_angular_velocity: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    prev_location: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    prev_rotation: mathutils.Quaternion
    """ 

    :type: mathutils.Quaternion
    """

    prev_velocity: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    rotation: mathutils.Quaternion
    """ 

    :type: mathutils.Quaternion
    """

    size: float
    """ 

    :type: float
    """

    velocity: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    def uv_on_emitter(self, modifier: ParticleSystemModifier) -> mathutils.Vector:
        """Obtain UV coordinates for a particle on an evaluated mesh.

        :param modifier: Particle modifier from an evaluated object
        :type modifier: ParticleSystemModifier
        :return: uv
        :rtype: mathutils.Vector
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
