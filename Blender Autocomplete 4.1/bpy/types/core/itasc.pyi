import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .ik_param import IKParam

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Itasc(IKParam, bpy_struct):
    """Parameters for the iTaSC IK solver"""

    damping_epsilon: float
    """ Singular value under which damping is progressively applied (higher values produce results with more stability, less reactivity)

    :type: float
    """

    damping_max: float
    """ Maximum damping coefficient when singular value is nearly 0 (higher values produce results with more stability, less reactivity)

    :type: float
    """

    feedback: float
    """ Feedback coefficient for error correction, average response time is 1/feedback

    :type: float
    """

    iterations: int
    """ Maximum number of iterations for convergence in case of reiteration

    :type: int
    """

    mode: str
    """ 

    :type: str
    """

    precision: float
    """ Precision of convergence in case of reiteration

    :type: float
    """

    reiteration_method: str
    """ Defines if the solver is allowed to reiterate (converge until precision is met) on none, first or all frames

    :type: str
    """

    solver: str
    """ Solving method selection: automatic damping or manual damping

    :type: str
    """

    step_count: int
    """ Divide the frame interval into this many steps

    :type: int
    """

    step_max: float
    """ Higher bound for timestep in second in case of automatic substeps

    :type: float
    """

    step_min: float
    """ Lower bound for timestep in second in case of automatic substeps

    :type: float
    """

    translate_root_bones: bool
    """ Translate root (i.e. parentless) bones to the armature origin

    :type: bool
    """

    use_auto_step: bool
    """ Automatically determine the optimal number of steps for best performance/accuracy trade off

    :type: bool
    """

    velocity_max: float
    """ Maximum joint velocity in radians/second

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
