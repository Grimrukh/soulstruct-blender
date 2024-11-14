import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ArmatureModifier(Modifier, bpy_struct):
    """Armature deformation modifier"""

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    object: Object
    """ Armature object to deform with

    :type: Object
    """

    use_bone_envelopes: bool
    """ Bind Bone envelopes to armature modifier

    :type: bool
    """

    use_deform_preserve_volume: bool
    """ Deform rotation interpolation with quaternions

    :type: bool
    """

    use_multi_modifier: bool
    """ Use same input as previous modifier, and mix results using overall vgroup

    :type: bool
    """

    use_vertex_groups: bool
    """ Bind vertex groups to armature modifier

    :type: bool
    """

    vertex_group: str
    """ Name of Vertex Group which determines influence of modifier per point

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
