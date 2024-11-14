import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ClothCollisionSettings(bpy_struct):
    """Cloth simulation settings for self collision and collision with other objects"""

    collection: Collection
    """ Limit colliders to this Collection

    :type: Collection
    """

    collision_quality: int
    """ How many collision iterations should be done. (higher is better quality but slower)

    :type: int
    """

    damping: float
    """ Amount of velocity lost on collision

    :type: float
    """

    distance_min: float
    """ Minimum distance between collision objects before collision response takes effect

    :type: float
    """

    friction: float
    """ Friction force if a collision happened (higher = less movement)

    :type: float
    """

    impulse_clamp: float
    """ Clamp collision impulses to avoid instability (0.0 to disable clamping)

    :type: float
    """

    self_distance_min: float
    """ Minimum distance between cloth faces before collision response takes effect

    :type: float
    """

    self_friction: float
    """ Friction with self contact

    :type: float
    """

    self_impulse_clamp: float
    """ Clamp collision impulses to avoid instability (0.0 to disable clamping)

    :type: float
    """

    use_collision: bool
    """ Enable collisions with other objects

    :type: bool
    """

    use_self_collision: bool
    """ Enable self collisions

    :type: bool
    """

    vertex_group_object_collisions: str
    """ Triangles with all vertices in this group are not used during object collisions

    :type: str
    """

    vertex_group_self_collisions: str
    """ Triangles with all vertices in this group are not used during self collisions

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
