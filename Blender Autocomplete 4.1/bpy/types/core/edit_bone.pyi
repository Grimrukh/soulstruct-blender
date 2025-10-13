import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .bone_collection import BoneCollection
from .bone_color import BoneColor

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class EditBone(bpy_struct):
    """Edit mode bone in an armature data-block"""

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

    bbone_custom_handle_end: EditBone
    """ Bone that serves as the end handle for the B-Bone curve

    :type: EditBone
    """

    bbone_custom_handle_start: EditBone
    """ Bone that serves as the start handle for the B-Bone curve

    :type: EditBone
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

    collections: bpy_prop_collection[BoneCollection]
    """ Bone Collections that contain this bone

    :type: bpy_prop_collection[BoneCollection]
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
    """ Location of head end of the bone

    :type: mathutils.Vector
    """

    head_radius: float
    """ Radius of head of bone (for Envelope deform only)

    :type: float
    """

    hide: bool
    """ Bone is not visible when in Edit Mode

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
    """ Length of the bone. Changing moves the tail end

    :type: float
    """

    lock: bool
    """ Bone is not able to be transformed when in Edit Mode

    :type: bool
    """

    matrix: mathutils.Matrix
    """ Matrix combining location and rotation of the bone (head position, direction and roll), in armature space (does not include/support bone's length/size)

    :type: mathutils.Matrix
    """

    name: str
    """ 

    :type: str
    """

    parent: EditBone
    """ Parent edit bone (in same Armature)

    :type: EditBone
    """

    roll: float
    """ Bone rotation around head-tail axis

    :type: float
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
    """ Location of tail end of the bone

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

    children: typing.Any
    """ A list of all the bones children.(readonly)"""

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

    def align_roll(
        self, vector: collections.abc.Sequence[float] | mathutils.Vector | None
    ):
        """Align the bone to a local-space roll so the Z axis points in the direction of the vector given

        :param vector: Vector
        :type vector: collections.abc.Sequence[float] | mathutils.Vector | None
        """
        ...

    def align_orientation(self, other):
        """Align this bone to another by moving its tail and settings its roll
        the length of the other bone is not used.

                :param other:
        """
        ...

    def parent_index(self, parent_test):
        """The same as 'bone in other_bone.parent_recursive'
        but saved generating a list.

                :param parent_test:
        """
        ...

    def transform(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        *,
        scale: bool | None = True,
        roll: bool | None = True,
    ):
        """Transform the the bones head, tail, roll and envelope
        (when the matrix has a scale component).

                :param matrix: 3x3 or 4x4 transformation matrix.
                :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
                :param scale: Scale the bone envelope by the matrix.
                :type scale: bool | None
                :param roll: Correct the roll to point in the same relative
        direction to the head and tail.
                :type roll: bool | None
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
