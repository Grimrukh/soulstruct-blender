import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RigidBodyConstraint(bpy_struct):
    """Constraint influencing Objects inside Rigid Body Simulation"""

    breaking_threshold: float
    """ Impulse threshold that must be reached for the constraint to break

    :type: float
    """

    disable_collisions: bool
    """ Disable collisions between constrained rigid bodies

    :type: bool
    """

    enabled: bool
    """ Enable this constraint

    :type: bool
    """

    limit_ang_x_lower: float
    """ Lower limit of X axis rotation

    :type: float
    """

    limit_ang_x_upper: float
    """ Upper limit of X axis rotation

    :type: float
    """

    limit_ang_y_lower: float
    """ Lower limit of Y axis rotation

    :type: float
    """

    limit_ang_y_upper: float
    """ Upper limit of Y axis rotation

    :type: float
    """

    limit_ang_z_lower: float
    """ Lower limit of Z axis rotation

    :type: float
    """

    limit_ang_z_upper: float
    """ Upper limit of Z axis rotation

    :type: float
    """

    limit_lin_x_lower: float
    """ Lower limit of X axis translation

    :type: float
    """

    limit_lin_x_upper: float
    """ Upper limit of X axis translation

    :type: float
    """

    limit_lin_y_lower: float
    """ Lower limit of Y axis translation

    :type: float
    """

    limit_lin_y_upper: float
    """ Upper limit of Y axis translation

    :type: float
    """

    limit_lin_z_lower: float
    """ Lower limit of Z axis translation

    :type: float
    """

    limit_lin_z_upper: float
    """ Upper limit of Z axis translation

    :type: float
    """

    motor_ang_max_impulse: float
    """ Maximum angular motor impulse

    :type: float
    """

    motor_ang_target_velocity: float
    """ Target angular motor velocity

    :type: float
    """

    motor_lin_max_impulse: float
    """ Maximum linear motor impulse

    :type: float
    """

    motor_lin_target_velocity: float
    """ Target linear motor velocity

    :type: float
    """

    object1: Object
    """ First Rigid Body Object to be constrained

    :type: Object
    """

    object2: Object
    """ Second Rigid Body Object to be constrained

    :type: Object
    """

    solver_iterations: int
    """ Number of constraint solver iterations made per simulation step (higher values are more accurate but slower)

    :type: int
    """

    spring_damping_ang_x: float
    """ Damping on the X rotational axis

    :type: float
    """

    spring_damping_ang_y: float
    """ Damping on the Y rotational axis

    :type: float
    """

    spring_damping_ang_z: float
    """ Damping on the Z rotational axis

    :type: float
    """

    spring_damping_x: float
    """ Damping on the X axis

    :type: float
    """

    spring_damping_y: float
    """ Damping on the Y axis

    :type: float
    """

    spring_damping_z: float
    """ Damping on the Z axis

    :type: float
    """

    spring_stiffness_ang_x: float
    """ Stiffness on the X rotational axis

    :type: float
    """

    spring_stiffness_ang_y: float
    """ Stiffness on the Y rotational axis

    :type: float
    """

    spring_stiffness_ang_z: float
    """ Stiffness on the Z rotational axis

    :type: float
    """

    spring_stiffness_x: float
    """ Stiffness on the X axis

    :type: float
    """

    spring_stiffness_y: float
    """ Stiffness on the Y axis

    :type: float
    """

    spring_stiffness_z: float
    """ Stiffness on the Z axis

    :type: float
    """

    spring_type: str
    """ Which implementation of spring to use

    :type: str
    """

    type: str
    """ Type of Rigid Body Constraint

    :type: str
    """

    use_breaking: bool
    """ Constraint can be broken if it receives an impulse above the threshold

    :type: bool
    """

    use_limit_ang_x: bool
    """ Limit rotation around X axis

    :type: bool
    """

    use_limit_ang_y: bool
    """ Limit rotation around Y axis

    :type: bool
    """

    use_limit_ang_z: bool
    """ Limit rotation around Z axis

    :type: bool
    """

    use_limit_lin_x: bool
    """ Limit translation on X axis

    :type: bool
    """

    use_limit_lin_y: bool
    """ Limit translation on Y axis

    :type: bool
    """

    use_limit_lin_z: bool
    """ Limit translation on Z axis

    :type: bool
    """

    use_motor_ang: bool
    """ Enable angular motor

    :type: bool
    """

    use_motor_lin: bool
    """ Enable linear motor

    :type: bool
    """

    use_override_solver_iterations: bool
    """ Override the number of solver iterations for this constraint

    :type: bool
    """

    use_spring_ang_x: bool
    """ Enable spring on X rotational axis

    :type: bool
    """

    use_spring_ang_y: bool
    """ Enable spring on Y rotational axis

    :type: bool
    """

    use_spring_ang_z: bool
    """ Enable spring on Z rotational axis

    :type: bool
    """

    use_spring_x: bool
    """ Enable spring on X axis

    :type: bool
    """

    use_spring_y: bool
    """ Enable spring on Y axis

    :type: bool
    """

    use_spring_z: bool
    """ Enable spring on Z axis

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
