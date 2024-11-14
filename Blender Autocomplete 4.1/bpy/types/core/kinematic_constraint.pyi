import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KinematicConstraint(Constraint, bpy_struct):
    """Inverse Kinematics"""

    chain_count: int
    """ How many bones are included in the IK effect - 0 uses all bones

    :type: int
    """

    distance: float
    """ Radius of limiting sphere

    :type: float
    """

    ik_type: str
    """ 

    :type: str
    """

    iterations: int
    """ Maximum number of solving iterations

    :type: int
    """

    limit_mode: str
    """ Distances in relation to sphere of influence to allow

    :type: str
    """

    lock_location_x: bool
    """ Constraint position along X axis

    :type: bool
    """

    lock_location_y: bool
    """ Constraint position along Y axis

    :type: bool
    """

    lock_location_z: bool
    """ Constraint position along Z axis

    :type: bool
    """

    lock_rotation_x: bool
    """ Constraint rotation along X axis

    :type: bool
    """

    lock_rotation_y: bool
    """ Constraint rotation along Y axis

    :type: bool
    """

    lock_rotation_z: bool
    """ Constraint rotation along Z axis

    :type: bool
    """

    orient_weight: float
    """ For Tree-IK: Weight of orientation control for this target

    :type: float
    """

    pole_angle: float
    """ Pole rotation offset

    :type: float
    """

    pole_subtarget: str
    """ 

    :type: str
    """

    pole_target: Object
    """ Object for pole rotation

    :type: Object
    """

    reference_axis: str
    """ Constraint axis Lock options relative to Bone or Target reference

    :type: str
    """

    subtarget: str
    """ Armature bone, mesh or lattice vertex group, ...

    :type: str
    """

    target: Object
    """ Target object

    :type: Object
    """

    use_location: bool
    """ Chain follows position of target

    :type: bool
    """

    use_rotation: bool
    """ Chain follows rotation of target

    :type: bool
    """

    use_stretch: bool
    """ Enable IK Stretching

    :type: bool
    """

    use_tail: bool
    """ Include bone's tail as last element in chain

    :type: bool
    """

    weight: float
    """ For Tree-IK: Weight of position control for this target

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
