import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .armature_edit_bones import ArmatureEditBones
from .struct import Struct
from .bpy_struct import bpy_struct
from .bone_collection import BoneCollection
from .anim_data import AnimData
from .id import ID
from .armature_bones import ArmatureBones

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Armature(ID, bpy_struct):
    """Armature data-block containing a hierarchy of bones, usually used for rigging characters"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    axes_position: float
    """ The position for the axes on the bone. Increasing the value moves it closer to the tip; decreasing moves it closer to the root

    :type: float
    """

    bones: ArmatureBones
    """ 

    :type: ArmatureBones
    """

    collections: typing.Any
    collections_all: bpy_prop_collection[BoneCollection]
    """ List of all bone collections of the armature

    :type: bpy_prop_collection[BoneCollection]
    """

    display_type: str
    """ 

    :type: str
    """

    edit_bones: ArmatureEditBones
    """ 

    :type: ArmatureEditBones
    """

    is_editmode: bool
    """ True when used in editmode

    :type: bool
    """

    pose_position: str
    """ Show armature in binding pose or final posed state

    :type: str
    """

    relation_line_position: str
    """ The start position of the relation lines from parent to child bones

    :type: str
    """

    show_axes: bool
    """ Display bone axes

    :type: bool
    """

    show_bone_colors: bool
    """ Display bone colors

    :type: bool
    """

    show_bone_custom_shapes: bool
    """ Display bones with their custom shapes

    :type: bool
    """

    show_names: bool
    """ Display bone names

    :type: bool
    """

    use_mirror_x: bool
    """ Apply changes to matching bone on opposite side of X-Axis

    :type: bool
    """

    def transform(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
    ):
        """Transform armature bones by a matrix

        :param matrix: Matrix
        :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
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
