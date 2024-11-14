import typing
import collections.abc
import mathutils
from .pose_bone_constraints import PoseBoneConstraints
from .motion_path import MotionPath
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .bone_color import BoneColor
from .object import Object
from .bone import Bone

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PoseBone(bpy_struct):
    """Channel defining pose data for a bone in a Pose"""

    bbone_curveinx: float
    """ X-axis handle offset for start of the B-Bone's curve, adjusts curvature

    :type: float
    """

    bbone_curveinz: float
    """ Z-axis handle offset for start of the B-Bone's curve, adjusts curvature

    :type: float
    """

    bbone_curveoutx: float
    """ X-axis handle offset for end of the B-Bone's curve, adjusts curvature

    :type: float
    """

    bbone_curveoutz: float
    """ Z-axis handle offset for end of the B-Bone's curve, adjusts curvature

    :type: float
    """

    bbone_custom_handle_end: PoseBone
    """ Bone that serves as the end handle for the B-Bone curve

    :type: PoseBone
    """

    bbone_custom_handle_start: PoseBone
    """ Bone that serves as the start handle for the B-Bone curve

    :type: PoseBone
    """

    bbone_easein: float
    """ Length of first Bézier Handle (for B-Bones only)

    :type: float
    """

    bbone_easeout: float
    """ Length of second Bézier Handle (for B-Bones only)

    :type: float
    """

    bbone_rollin: float
    """ Roll offset for the start of the B-Bone, adjusts twist

    :type: float
    """

    bbone_rollout: float
    """ Roll offset for the end of the B-Bone, adjusts twist

    :type: float
    """

    bbone_scalein: mathutils.Vector
    """ Scale factors for the start of the B-Bone, adjusts thickness (for tapering effects)

    :type: mathutils.Vector
    """

    bbone_scaleout: mathutils.Vector
    """ Scale factors for the end of the B-Bone, adjusts thickness (for tapering effects)

    :type: mathutils.Vector
    """

    bone: Bone
    """ Bone associated with this PoseBone

    :type: Bone
    """

    child: PoseBone
    """ Child of this pose bone

    :type: PoseBone
    """

    color: BoneColor
    """ 

    :type: BoneColor
    """

    constraints: PoseBoneConstraints
    """ Constraints that act on this pose channel

    :type: PoseBoneConstraints
    """

    custom_shape: Object
    """ Object that defines custom display shape for this bone

    :type: Object
    """

    custom_shape_rotation_euler: mathutils.Euler
    """ Adjust the rotation of the custom shape

    :type: mathutils.Euler
    """

    custom_shape_scale_xyz: mathutils.Vector
    """ Adjust the size of the custom shape

    :type: mathutils.Vector
    """

    custom_shape_transform: PoseBone
    """ Bone that defines the display transform of this custom shape

    :type: PoseBone
    """

    custom_shape_translation: mathutils.Vector
    """ Adjust the location of the custom shape

    :type: mathutils.Vector
    """

    head: mathutils.Vector
    """ Location of head of the channel's bone

    :type: mathutils.Vector
    """

    ik_linear_weight: float
    """ Weight of scale constraint for IK

    :type: float
    """

    ik_max_x: float
    """ Maximum angles for IK Limit

    :type: float
    """

    ik_max_y: float
    """ Maximum angles for IK Limit

    :type: float
    """

    ik_max_z: float
    """ Maximum angles for IK Limit

    :type: float
    """

    ik_min_x: float
    """ Minimum angles for IK Limit

    :type: float
    """

    ik_min_y: float
    """ Minimum angles for IK Limit

    :type: float
    """

    ik_min_z: float
    """ Minimum angles for IK Limit

    :type: float
    """

    ik_rotation_weight: float
    """ Weight of rotation constraint for IK

    :type: float
    """

    ik_stiffness_x: float
    """ IK stiffness around the X axis

    :type: float
    """

    ik_stiffness_y: float
    """ IK stiffness around the Y axis

    :type: float
    """

    ik_stiffness_z: float
    """ IK stiffness around the Z axis

    :type: float
    """

    ik_stretch: float
    """ Allow scaling of the bone for IK

    :type: float
    """

    is_in_ik_chain: bool
    """ Is part of an IK chain

    :type: bool
    """

    length: float
    """ Length of the bone

    :type: float
    """

    location: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    lock_ik_x: bool
    """ Disallow movement around the X axis

    :type: bool
    """

    lock_ik_y: bool
    """ Disallow movement around the Y axis

    :type: bool
    """

    lock_ik_z: bool
    """ Disallow movement around the Z axis

    :type: bool
    """

    lock_location: list[bool]
    """ Lock editing of location when transforming

    :type: list[bool]
    """

    lock_rotation: list[bool]
    """ Lock editing of rotation when transforming

    :type: list[bool]
    """

    lock_rotation_w: bool
    """ Lock editing of 'angle' component of four-component rotations when transforming

    :type: bool
    """

    lock_rotations_4d: bool
    """ Lock editing of four component rotations by components (instead of as Eulers)

    :type: bool
    """

    lock_scale: list[bool]
    """ Lock editing of scale when transforming

    :type: list[bool]
    """

    matrix: mathutils.Matrix
    """ Final 4×4 matrix after constraints and drivers are applied, in the armature object space

    :type: mathutils.Matrix
    """

    matrix_basis: mathutils.Matrix
    """ Alternative access to location/scale/rotation relative to the parent and own rest bone

    :type: mathutils.Matrix
    """

    matrix_channel: mathutils.Matrix
    """ 4×4 matrix of the bone's location/rotation/scale channels (including animation and drivers) and the effect of bone constraints

    :type: mathutils.Matrix
    """

    motion_path: MotionPath
    """ Motion Path for this element

    :type: MotionPath
    """

    name: str
    """ 

    :type: str
    """

    parent: PoseBone
    """ Parent of this pose bone

    :type: PoseBone
    """

    rotation_axis_angle: bpy_prop_array[float]
    """ Angle of Rotation for Axis-Angle rotation representation

    :type: bpy_prop_array[float]
    """

    rotation_euler: mathutils.Euler
    """ Rotation in Eulers

    :type: mathutils.Euler
    """

    rotation_mode: str
    """ 

    :type: str
    """

    rotation_quaternion: mathutils.Quaternion
    """ Rotation in Quaternions

    :type: mathutils.Quaternion
    """

    scale: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    tail: mathutils.Vector
    """ Location of tail of the channel's bone

    :type: mathutils.Vector
    """

    use_custom_shape_bone_size: bool
    """ Scale the custom object by the bone length

    :type: bool
    """

    use_ik_limit_x: bool
    """ Limit movement around the X axis

    :type: bool
    """

    use_ik_limit_y: bool
    """ Limit movement around the Y axis

    :type: bool
    """

    use_ik_limit_z: bool
    """ Limit movement around the Z axis

    :type: bool
    """

    use_ik_linear_control: bool
    """ Apply channel size as IK constraint if stretching is enabled

    :type: bool
    """

    use_ik_rotation_control: bool
    """ Apply channel rotation as IK constraint

    :type: bool
    """

    basename: typing.Any
    """ The name of this bone before any '.' character(readonly)"""

    center: typing.Any
    """ The midpoint between the head and the tail.(readonly)"""

    children: typing.Any
    """ (readonly)"""

    children_recursive: typing.Any
    """ A list of all children from this bone.(readonly)"""

    children_recursive_basename: typing.Any
    """ Returns a chain of children with the same base name as this bone.
Only direct chains are supported, forks caused by multiple children
with matching base names will terminate the function
and not be returned.(readonly)"""

    parent_recursive: typing.Any
    """ A list of parents, starting with the immediate parent(readonly)"""

    vector: typing.Any
    """ The direction this bone is pointing.
Utility function for (tail - head)(readonly)"""

    x_axis: typing.Any
    """ Vector pointing down the x-axis of the bone.(readonly)"""

    y_axis: typing.Any
    """ Vector pointing down the y-axis of the bone.(readonly)"""

    z_axis: typing.Any
    """ Vector pointing down the z-axis of the bone.(readonly)"""

    def evaluate_envelope(
        self, point: collections.abc.Sequence[float] | mathutils.Vector | None
    ) -> float:
        """Calculate bone envelope at given point

        :param point: Point, Position in 3d space to evaluate
        :type point: collections.abc.Sequence[float] | mathutils.Vector | None
        :return: Factor, Envelope factor
        :rtype: float
        """
        ...

    def bbone_segment_index(
        self, point: collections.abc.Sequence[float] | mathutils.Vector | None
    ):
        """Retrieve the index and blend factor of the B-Bone segments based on vertex position

                :param point: Point, Vertex position in armature pose space
                :type point: collections.abc.Sequence[float] | mathutils.Vector | None
                :return: index, The index of the first segment joint affecting the point, int in [-inf, inf]

        blend_next, The blend factor between the given and the following joint, float in [-inf, inf]
        """
        ...

    def bbone_segment_matrix(
        self, index: int | None, rest: bool | typing.Any | None = False
    ) -> mathutils.Matrix:
        """Retrieve the matrix of the joint between B-Bone segments if availableThis example shows how to use B-Bone segment matrices to emulate deformation
        produced by the Armature modifier or constraint when assigned to the given bone
        (without Preserve Volume). The coordinates are processed in armature Pose space:

                :param index: Index of the segment endpoint
                :type index: int | None
                :param rest: Return the rest pose matrix
                :type rest: bool | typing.Any | None
                :return: The resulting matrix in bone local space
                :rtype: mathutils.Matrix
        """
        ...

    def compute_bbone_handles(
        self,
        rest: bool | typing.Any | None = False,
        ease: bool | typing.Any | None = False,
        offsets: bool | typing.Any | None = False,
    ):
        """Retrieve the vectors and rolls coming from B-Bone custom handles

                :param rest: Return the rest pose state
                :type rest: bool | typing.Any | None
                :param ease: Apply scale from ease values
                :type ease: bool | typing.Any | None
                :param offsets: Apply roll and curve offsets from bone properties
                :type offsets: bool | typing.Any | None
                :return: handle1, The direction vector of the start handle in bone local space, `mathutils.Vector` of 3 items in [-inf, inf]

        roll1, Roll of the start handle, float in [-inf, inf]

        handle2, The direction vector of the end handle in bone local space, `mathutils.Vector` of 3 items in [-inf, inf]

        roll2, Roll of the end handle, float in [-inf, inf]
        """
        ...

    def parent_index(self, parent_test):
        """The same as 'bone in other_bone.parent_recursive'
        but saved generating a list.

                :param parent_test:
        """
        ...

    def translate(self, vec):
        """Utility function to add vec to the head and tail of this bone

        :param vec:
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
