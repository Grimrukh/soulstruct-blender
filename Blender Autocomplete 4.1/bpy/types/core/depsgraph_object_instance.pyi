import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .particle_system import ParticleSystem
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DepsgraphObjectInstance(bpy_struct):
    """Extended information about dependency graph object iterator (Warning: All data here is 'evaluated' one, not original .blend IDs)"""

    instance_object: Object
    """ Evaluated object which is being instanced by this iterator

    :type: Object
    """

    is_instance: bool
    """ Denotes if the object is generated by another object

    :type: bool
    """

    matrix_world: mathutils.Matrix
    """ Generated transform matrix in world space

    :type: mathutils.Matrix
    """

    object: Object
    """ Evaluated object the iterator points to

    :type: Object
    """

    orco: mathutils.Vector
    """ Generated coordinates in parent object space

    :type: mathutils.Vector
    """

    parent: Object
    """ If the object is an instance, the parent object that generated it

    :type: Object
    """

    particle_system: ParticleSystem
    """ Evaluated particle system that this object was instanced from

    :type: ParticleSystem
    """

    persistent_id: bpy_prop_array[int]
    """ Persistent identifier for inter-frame matching of objects with motion blur

    :type: bpy_prop_array[int]
    """

    random_id: int
    """ Random id for this instance, typically for randomized shading

    :type: int
    """

    show_particles: bool
    """ Particles part of the object should be visible in the render

    :type: bool
    """

    show_self: bool
    """ The object geometry itself should be visible in the render

    :type: bool
    """

    uv: bpy_prop_array[float]
    """ UV coordinates in parent object space

    :type: bpy_prop_array[float]
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