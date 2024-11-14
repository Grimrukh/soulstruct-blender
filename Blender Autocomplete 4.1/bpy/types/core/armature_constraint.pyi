import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .armature_constraint_targets import ArmatureConstraintTargets

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ArmatureConstraint(Constraint, bpy_struct):
    """Applies transformations done by the Armature modifier"""

    targets: ArmatureConstraintTargets
    """ Target Bones

    :type: ArmatureConstraintTargets
    """

    use_bone_envelopes: bool
    """ Multiply weights by envelope for all bones, instead of acting like Vertex Group based blending. The specified weights are still used, and only the listed bones are considered

    :type: bool
    """

    use_current_location: bool
    """ Use the current bone location for envelopes and choosing B-Bone segments instead of rest position

    :type: bool
    """

    use_deform_preserve_volume: bool
    """ Deform rotation interpolation with quaternions

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
