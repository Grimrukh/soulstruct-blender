import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .effector_weights import EffectorWeights

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SoftBodySettings(bpy_struct):
    """Soft body simulation settings for an object"""

    aero: int
    """ Make edges 'sail'

    :type: int
    """

    aerodynamics_type: str
    """ Method of calculating aerodynamic interaction

    :type: str
    """

    ball_damp: float
    """ Blending to inelastic collision

    :type: float
    """

    ball_size: float
    """ Absolute ball size or factor if not manually adjusted

    :type: float
    """

    ball_stiff: float
    """ Ball inflating pressure

    :type: float
    """

    bend: float
    """ Bending Stiffness

    :type: float
    """

    choke: int
    """ 'Viscosity' inside collision target

    :type: int
    """

    collision_collection: Collection
    """ Limit colliders to this collection

    :type: Collection
    """

    collision_type: str
    """ Choose Collision Type

    :type: str
    """

    damping: float
    """ Edge spring friction

    :type: float
    """

    effector_weights: EffectorWeights
    """ 

    :type: EffectorWeights
    """

    error_threshold: float
    """ The Runge-Kutta ODE solver error limit, low value gives more precision, high values speed

    :type: float
    """

    friction: float
    """ General media friction for point movements

    :type: float
    """

    fuzzy: int
    """ Fuzziness while on collision, high values make collision handling faster but less stable

    :type: int
    """

    goal_default: float
    """ Default Goal (vertex target position) value

    :type: float
    """

    goal_friction: float
    """ Goal (vertex target position) friction

    :type: float
    """

    goal_max: float
    """ Goal maximum, vertex weights are scaled to match this range

    :type: float
    """

    goal_min: float
    """ Goal minimum, vertex weights are scaled to match this range

    :type: float
    """

    goal_spring: float
    """ Goal (vertex target position) spring stiffness

    :type: float
    """

    gravity: float
    """ Apply gravitation to point movement

    :type: float
    """

    location_mass_center: mathutils.Vector
    """ Location of center of mass

    :type: mathutils.Vector
    """

    mass: float
    """ General Mass value

    :type: float
    """

    plastic: int
    """ Permanent deform

    :type: int
    """

    pull: float
    """ Edge spring stiffness when longer than rest length

    :type: float
    """

    push: float
    """ Edge spring stiffness when shorter than rest length

    :type: float
    """

    rotation_estimate: mathutils.Matrix
    """ Estimated rotation matrix

    :type: mathutils.Matrix
    """

    scale_estimate: mathutils.Matrix
    """ Estimated scale matrix

    :type: mathutils.Matrix
    """

    shear: float
    """ Shear Stiffness

    :type: float
    """

    speed: float
    """ Tweak timing for physics to control frequency and speed

    :type: float
    """

    spring_length: int
    """ Alter spring length to shrink/blow up (unit %) 0 to disable

    :type: int
    """

    step_max: int
    """ Maximal # solver steps/frame

    :type: int
    """

    step_min: int
    """ Minimal # solver steps/frame

    :type: int
    """

    use_auto_step: bool
    """ Use velocities for automagic step sizes

    :type: bool
    """

    use_diagnose: bool
    """ Turn on SB diagnose console prints

    :type: bool
    """

    use_edge_collision: bool
    """ Edges collide too

    :type: bool
    """

    use_edges: bool
    """ Use Edges as springs

    :type: bool
    """

    use_estimate_matrix: bool
    """ Store the estimated transforms in the soft body settings

    :type: bool
    """

    use_face_collision: bool
    """ Faces collide too, can be very slow

    :type: bool
    """

    use_goal: bool
    """ Define forces for vertices to stick to animated position

    :type: bool
    """

    use_self_collision: bool
    """ Enable naive vertex ball self collision

    :type: bool
    """

    use_stiff_quads: bool
    """ Add diagonal springs on 4-gons

    :type: bool
    """

    vertex_group_goal: str
    """ Control point weight values

    :type: str
    """

    vertex_group_mass: str
    """ Control point mass values

    :type: str
    """

    vertex_group_spring: str
    """ Control point spring strength values

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
