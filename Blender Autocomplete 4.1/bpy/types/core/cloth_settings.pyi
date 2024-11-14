import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .shape_key import ShapeKey
from .effector_weights import EffectorWeights

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ClothSettings(bpy_struct):
    """Cloth simulation settings for an object"""

    air_damping: float
    """ Air has normally some thickness which slows falling things down

    :type: float
    """

    bending_damping: float
    """ Amount of damping in bending behavior

    :type: float
    """

    bending_model: str
    """ Physical model for simulating bending forces

    :type: str
    """

    bending_stiffness: float
    """ How much the material resists bending

    :type: float
    """

    bending_stiffness_max: float
    """ Maximum bending stiffness value

    :type: float
    """

    collider_friction: float
    """ 

    :type: float
    """

    compression_damping: float
    """ Amount of damping in compression behavior

    :type: float
    """

    compression_stiffness: float
    """ How much the material resists compression

    :type: float
    """

    compression_stiffness_max: float
    """ Maximum compression stiffness value

    :type: float
    """

    density_strength: float
    """ Influence of target density on the simulation

    :type: float
    """

    density_target: float
    """ Maximum density of hair

    :type: float
    """

    effector_weights: EffectorWeights
    """ 

    :type: EffectorWeights
    """

    fluid_density: float
    """ Density (kg/l) of the fluid contained inside the object, used to create a hydrostatic pressure gradient simulating the weight of the internal fluid, or buoyancy from the surrounding fluid if negative

    :type: float
    """

    goal_default: float
    """ Default Goal (vertex target position) value, when no Vertex Group used

    :type: float
    """

    goal_friction: float
    """ Goal (vertex target position) friction

    :type: float
    """

    goal_max: float
    """ Goal maximum, vertex group weights are scaled to match this range

    :type: float
    """

    goal_min: float
    """ Goal minimum, vertex group weights are scaled to match this range

    :type: float
    """

    goal_spring: float
    """ Goal (vertex target position) spring stiffness

    :type: float
    """

    gravity: mathutils.Vector
    """ Gravity or external force vector

    :type: mathutils.Vector
    """

    internal_compression_stiffness: float
    """ How much the material resists compression

    :type: float
    """

    internal_compression_stiffness_max: float
    """ Maximum compression stiffness value

    :type: float
    """

    internal_friction: float
    """ 

    :type: float
    """

    internal_spring_max_diversion: float
    """ How much the rays used to connect the internal points can diverge from the vertex normal

    :type: float
    """

    internal_spring_max_length: float
    """ The maximum length an internal spring can have during creation. If the distance between internal points is greater than this, no internal spring will be created between these points. A length of zero means that there is no length limit

    :type: float
    """

    internal_spring_normal_check: bool
    """ Require the points the internal springs connect to have opposite normal directions

    :type: bool
    """

    internal_tension_stiffness: float
    """ How much the material resists stretching

    :type: float
    """

    internal_tension_stiffness_max: float
    """ Maximum tension stiffness value

    :type: float
    """

    mass: float
    """ The mass of each vertex on the cloth material

    :type: float
    """

    pin_stiffness: float
    """ Pin (vertex target position) spring stiffness

    :type: float
    """

    pressure_factor: float
    """ Ambient pressure (kPa) that balances out between the inside and outside of the object when it has the target volume

    :type: float
    """

    quality: int
    """ Quality of the simulation in steps per frame (higher is better quality but slower)

    :type: int
    """

    rest_shape_key: ShapeKey
    """ Shape key to use the rest spring lengths from

    :type: ShapeKey
    """

    sewing_force_max: float
    """ Maximum sewing force

    :type: float
    """

    shear_damping: float
    """ Amount of damping in shearing behavior

    :type: float
    """

    shear_stiffness: float
    """ How much the material resists shearing

    :type: float
    """

    shear_stiffness_max: float
    """ Maximum shear scaling value

    :type: float
    """

    shrink_max: float
    """ Max amount to shrink cloth by

    :type: float
    """

    shrink_min: float
    """ Factor by which to shrink cloth

    :type: float
    """

    target_volume: float
    """ The mesh volume where the inner/outer pressure will be the same. If set to zero the change in volume will not affect pressure

    :type: float
    """

    tension_damping: float
    """ Amount of damping in stretching behavior

    :type: float
    """

    tension_stiffness: float
    """ How much the material resists stretching

    :type: float
    """

    tension_stiffness_max: float
    """ Maximum tension stiffness value

    :type: float
    """

    time_scale: float
    """ Cloth speed is multiplied by this value

    :type: float
    """

    uniform_pressure_force: float
    """ The uniform pressure that is constantly applied to the mesh, in units of Pressure Scale. Can be negative

    :type: float
    """

    use_dynamic_mesh: bool
    """ Make simulation respect deformations in the base mesh

    :type: bool
    """

    use_internal_springs: bool
    """ Simulate an internal volume structure by creating springs connecting the opposite sides of the mesh

    :type: bool
    """

    use_pressure: bool
    """ Simulate pressure inside a closed cloth mesh

    :type: bool
    """

    use_pressure_volume: bool
    """ Use the Target Volume parameter as the initial volume, instead of calculating it from the mesh itself

    :type: bool
    """

    use_sewing_springs: bool
    """ Pulls loose edges together

    :type: bool
    """

    vertex_group_bending: str
    """ Vertex group for fine control over bending stiffness

    :type: str
    """

    vertex_group_intern: str
    """ Vertex group for fine control over the internal spring stiffness

    :type: str
    """

    vertex_group_mass: str
    """ Vertex Group for pinning of vertices

    :type: str
    """

    vertex_group_pressure: str
    """ Vertex Group for where to apply pressure. Zero weight means no pressure while a weight of one means full pressure. Faces with a vertex that has zero weight will be excluded from the volume calculation

    :type: str
    """

    vertex_group_shear_stiffness: str
    """ Vertex group for fine control over shear stiffness

    :type: str
    """

    vertex_group_shrink: str
    """ Vertex Group for shrinking cloth

    :type: str
    """

    vertex_group_structural_stiffness: str
    """ Vertex group for fine control over structural stiffness

    :type: str
    """

    voxel_cell_size: float
    """ Size of the voxel grid cells for interaction effects

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
