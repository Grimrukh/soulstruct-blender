import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .effector_weights import EffectorWeights
from .point_cache import PointCache
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RigidBodyWorld(bpy_struct):
    """Self-contained rigid body simulation environment and settings"""

    collection: Collection
    """ Collection containing objects participating in this simulation

    :type: Collection
    """

    constraints: Collection
    """ Collection containing rigid body constraint objects

    :type: Collection
    """

    effector_weights: EffectorWeights
    """ 

    :type: EffectorWeights
    """

    enabled: bool
    """ Simulation will be evaluated

    :type: bool
    """

    point_cache: PointCache
    """ 

    :type: PointCache
    """

    solver_iterations: int
    """ Number of constraint solver iterations made per simulation step (higher values are more accurate but slower)

    :type: int
    """

    substeps_per_frame: int
    """ Number of simulation steps taken per frame (higher values are more accurate but slower)

    :type: int
    """

    time_scale: float
    """ Change the speed of the simulation

    :type: float
    """

    use_split_impulse: bool
    """ Reduce extra velocity that can build up when objects collide (lowers simulation stability a little so use only when necessary)

    :type: bool
    """

    def convex_sweep_test(
        self,
        object: Object,
        start: collections.abc.Sequence[float] | mathutils.Vector | None,
        end: collections.abc.Sequence[float] | mathutils.Vector | None,
    ):
        """Sweep test convex rigidbody against the current rigidbody world

                :param object: Rigidbody object with a convex collision shape
                :type object: Object
                :param start:
                :type start: collections.abc.Sequence[float] | mathutils.Vector | None
                :param end:
                :type end: collections.abc.Sequence[float] | mathutils.Vector | None
                :return: object_location, The hit location of this sweep test, `mathutils.Vector` of 3 items in [-inf, inf]

        hitpoint, The hit location of this sweep test, `mathutils.Vector` of 3 items in [-inf, inf]

        normal, The face normal at the sweep test hit location, `mathutils.Vector` of 3 items in [-inf, inf]

        has_hit, If the function has found collision point, value is 1, otherwise 0, int in [-inf, inf]
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
