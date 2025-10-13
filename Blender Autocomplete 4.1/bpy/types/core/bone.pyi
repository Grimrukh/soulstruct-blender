import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bone_collection_memberships import BoneCollectionMemberships
from .bpy_struct import bpy_struct
from .bone_color import BoneColor

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")

if typing.TYPE_CHECKING:
    from io_soulstruct import *


class Bone(bpy_struct):
    """Bone in an Armature data-block"""

    # region Soulstruct Extensions
    FLVER_BONE: FLVERBoneProps
    # endregion

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

    bbone_custom_handle_end: Bone
    """ Bone that serves as the end handle for the B-Bone curve

    :type: Bone
    """

    bbone_custom_handle_start: Bone
    """ Bone that serves as the start handle for the B-Bone curve

    :type: Bone
    """

    bbone_easein: float
    """ Length of first Bézier Handle (for B-Bones only)

    :type: float
    """

    bbone_easeout: float
    """ Length of second Bézier Handle (for B-Bones only)

    :type: float
    """

    bbone_handle_type_end: str
    """ Selects how the end handle of the B-Bone is computed

    :type: str
    """

    bbone_handle_type_start: str
    """ Selects how the start handle of the B-Bone is computed

    :type: str
    """

    bbone_handle_use_ease_end: bool
    """ Multiply the B-Bone Ease Out channel by the local Y scale value of the end handle. This is done after the Scale Easing option and isn't affected by it

    :type: bool
    """

    bbone_handle_use_ease_start: bool
    """ Multiply the B-Bone Ease In channel by the local Y scale value of the start handle. This is done after the Scale Easing option and isn't affected by it

    :type: bool
    """

    bbone_handle_use_scale_end: list[bool]
    """ Multiply B-Bone Scale Out channels by the local scale values of the end handle. This is done after the Scale Easing option and isn't affected by it

    :type: list[bool]
    """

    bbone_handle_use_scale_start: list[bool]
    """ Multiply B-Bone Scale In channels by the local scale values of the start handle. This is done after the Scale Easing option and isn't affected by it

    :type: list[bool]
    """

    bbone_mapping_mode: str
    """ Selects how the vertices are mapped to B-Bone segments based on their position

    :type: str
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

    bbone_segments: int
    """ Number of subdivisions of bone (for B-Bones only)

    :type: int
    """

    bbone_x: float
    """ B-Bone X size

    :type: float
    """

    bbone_z: float
    """ B-Bone Z size

    :type: float
    """

    children: bpy_prop_collection[Bone]
    """ Bones which are children of this bone

    :type: bpy_prop_collection[Bone]
    """

    collections: BoneCollectionMemberships
    """ Bone Collections that contain this bone

    :type: BoneCollectionMemberships
    """

    color: BoneColor
    """ 

    :type: BoneColor
    """

    envelope_distance: float
    """ Bone deformation distance (for Envelope deform only)

    :type: float
    """

    envelope_weight: float
    """ Bone deformation weight (for Envelope deform only)

    :type: float
    """

    head: mathutils.Vector
    """ Location of head end of the bone relative to its parent

    :type: mathutils.Vector
    """

    head_local: mathutils.Vector
    """ Location of head end of the bone relative to armature

    :type: mathutils.Vector
    """

    head_radius: float
    """ Radius of head of bone (for Envelope deform only)

    :type: float
    """

    hide: bool
    """ Bone is not visible when it is not in Edit Mode (i.e. in Object or Pose Modes)

    :type: bool
    """

    hide_select: bool
    """ Bone is able to be selected

    :type: bool
    """

    inherit_scale: str
    """ Specifies how the bone inherits scaling from the parent bone

    :type: str
    """

    length: float
    """ Length of the bone

    :type: float
    """

    matrix: mathutils.Matrix
    """ 3×3 bone matrix

    :type: mathutils.Matrix
    """

    matrix_local: mathutils.Matrix
    """ 4×4 bone matrix relative to armature (NOT parent bone)

    :type: mathutils.Matrix
    """

    name: str
    """ 

    :type: str
    """

    parent: Bone
    """ Parent bone (in same Armature)

    :type: Bone
    """

    select: bool
    """ 

    :type: bool
    """

    select_head: bool
    """ 

    :type: bool
    """

    select_tail: bool
    """ 

    :type: bool
    """

    show_wire: bool
    """ Bone is always displayed in wireframe regardless of viewport shading mode (useful for non-obstructive custom bone shapes)

    :type: bool
    """

    tail: mathutils.Vector
    """ Location of tail end of the bone relative to its parent

    :type: mathutils.Vector
    """

    tail_local: mathutils.Vector
    """ Location of tail end of the bone relative to armature

    :type: mathutils.Vector
    """

    tail_radius: float
    """ Radius of tail of bone (for Envelope deform only)

    :type: float
    """

    use_connect: bool
    """ When bone has a parent, bone's head is stuck to the parent's tail

    :type: bool
    """

    use_cyclic_offset: bool
    """ When bone doesn't have a parent, it receives cyclic offset effects (Deprecated)

    :type: bool
    """

    use_deform: bool
    """ Enable Bone to deform geometry

    :type: bool
    """

    use_endroll_as_inroll: bool
    """ Add Roll Out of the Start Handle bone to the Roll In value

    :type: bool
    """

    use_envelope_multiply: bool
    """ When deforming bone, multiply effects of Vertex Group weights with Envelope influence

    :type: bool
    """

    use_inherit_rotation: bool
    """ Bone inherits rotation or scale from parent bone

    :type: bool
    """

    use_local_location: bool
    """ Bone location is set in local space

    :type: bool
    """

    use_relative_parent: bool
    """ Object children will use relative transform, like deform

    :type: bool
    """

    use_scale_easing: bool
    """ Multiply the final easing values by the Scale In/Out Y factors

    :type: bool
    """

    basename: typing.Any
    """ The name of this bone before any '.' character(readonly)"""

    center: typing.Any
    """ The midpoint between the head and the tail.(readonly)"""

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

    def convert_local_to_pose(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        matrix_local: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        parent_matrix: typing.Any | None = (
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
        ),
        parent_matrix_local: typing.Any | None = (
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
        ),
        invert: bool | typing.Any | None = False,
    ) -> mathutils.Matrix:
        """Transform a matrix from Local to Pose space (or back), taking into account options like Inherit Scale and Local Location. Unlike Object.convert_space, this uses custom rest and pose matrices provided by the caller. If the parent matrices are omitted, the bone is assumed to have no parent.This method enables conversions between Local and Pose space for bones in
        the middle of updating the armature without having to update dependencies
        after each change, by manually carrying updated matrices in a recursive walk.

                :param matrix: The matrix to transform
                :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
                :param matrix_local: The custom rest matrix of this bone (Bone.matrix_local)
                :type matrix_local: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
                :param parent_matrix: The custom pose matrix of the parent bone (PoseBone.matrix)
                :type parent_matrix: typing.Any | None
                :param parent_matrix_local: The custom rest matrix of the parent bone (Bone.matrix_local)
                :type parent_matrix_local: typing.Any | None
                :param invert: Convert from Pose to Local space
                :type invert: bool | typing.Any | None
                :return: The transformed matrix
                :rtype: mathutils.Matrix
        """
        ...

    @classmethod
    def MatrixFromAxisRoll(
        cls, axis: typing.Any, roll: float | None
    ) -> mathutils.Matrix:
        """Convert the axis + roll representation to a matrix

        :param axis: The main axis of the bone (tail - head)
        :type axis: typing.Any
        :param roll: The roll of the bone
        :type roll: float | None
        :return: The resulting orientation matrix
        :rtype: mathutils.Matrix
        """
        ...

    @classmethod
    def AxisRollFromMatrix(
        cls, matrix: typing.Any, axis: typing.Any | None = (0.0, 0.0, 0.0)
    ):
        """Convert a rotational matrix to the axis + roll representation. Note that the resulting value of the roll may not be as expected if the matrix has shear or negative determinant.

                :param matrix: The orientation matrix of the bone
                :type matrix: typing.Any
                :param axis: The optional override for the axis (finds closest approximation for the matrix)
                :type axis: typing.Any | None
                :return: result_axis, The main axis of the bone, `mathutils.Vector` of 3 items in [-inf, inf]

        result_roll, The roll of the bone, float in [-inf, inf]
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
