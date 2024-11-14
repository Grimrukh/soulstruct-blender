import typing
import collections.abc
import mathutils
from .particle_system_modifier import ParticleSystemModifier
from .particle import Particle
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ParticleHairKey(bpy_struct):
    """Particle key for hair particle system"""

    co: mathutils.Vector
    """ Location of the hair key in object space

    :type: mathutils.Vector
    """

    co_local: mathutils.Vector
    """ Location of the hair key in its local coordinate system, relative to the emitting face

    :type: mathutils.Vector
    """

    time: float
    """ Relative time of key over hair length

    :type: float
    """

    weight: float
    """ Weight for cloth simulation

    :type: float
    """

    def co_object(
        self, object: Object, modifier: ParticleSystemModifier, particle: Particle
    ) -> mathutils.Vector:
        """Obtain hairkey location with particle and modifier data

        :param object: Object
        :type object: Object
        :param modifier: Particle modifier
        :type modifier: ParticleSystemModifier
        :param particle: hair particle
        :type particle: Particle
        :return: Co, Exported hairkey location
        :rtype: mathutils.Vector
        """
        ...

    def co_object_set(
        self,
        object: Object,
        modifier: ParticleSystemModifier,
        particle: Particle,
        co: collections.abc.Sequence[float] | mathutils.Vector | None,
    ):
        """Set hairkey location with particle and modifier data

        :param object: Object
        :type object: Object
        :param modifier: Particle modifier
        :type modifier: ParticleSystemModifier
        :param particle: hair particle
        :type particle: Particle
        :param co: Co, Specified hairkey location
        :type co: collections.abc.Sequence[float] | mathutils.Vector | None
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
