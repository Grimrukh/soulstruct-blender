import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .particle_system import ParticleSystem
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ParticleInstanceModifier(Modifier, bpy_struct):
    """Particle system instancing modifier"""

    axis: str
    """ Pole axis for rotation

    :type: str
    """

    index_layer_name: str
    """ Custom data layer name for the index

    :type: str
    """

    object: Object
    """ Object that has the particle system

    :type: Object
    """

    particle_amount: float
    """ Amount of particles to use for instancing

    :type: float
    """

    particle_offset: float
    """ Relative offset of particles to use for instancing, to avoid overlap of multiple instances

    :type: float
    """

    particle_system: ParticleSystem
    """ 

    :type: ParticleSystem
    """

    particle_system_index: int
    """ 

    :type: int
    """

    position: float
    """ Position along path

    :type: float
    """

    random_position: float
    """ Randomize position along path

    :type: float
    """

    random_rotation: float
    """ Randomize rotation around path

    :type: float
    """

    rotation: float
    """ Rotation around path

    :type: float
    """

    show_alive: bool
    """ Show instances when particles are alive

    :type: bool
    """

    show_dead: bool
    """ Show instances when particles are dead

    :type: bool
    """

    show_unborn: bool
    """ Show instances when particles are unborn

    :type: bool
    """

    space: str
    """ Space to use for copying mesh data

    :type: str
    """

    use_children: bool
    """ Create instances from child particles

    :type: bool
    """

    use_normal: bool
    """ Create instances from normal particles

    :type: bool
    """

    use_path: bool
    """ Create instances along particle paths

    :type: bool
    """

    use_preserve_shape: bool
    """ Don't stretch the object

    :type: bool
    """

    use_size: bool
    """ Use particle size to scale the instances

    :type: bool
    """

    value_layer_name: str
    """ Custom data layer name for the randomized value

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
