import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .edit_bone import EditBone
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ArmatureEditBones(bpy_prop_collection[EditBone], bpy_struct):
    """Collection of armature edit bones"""

    active: EditBone | None
    """ Armatures active edit bone

    :type: EditBone | None
    """

    def new(self, name: str | typing.Any) -> EditBone:
        """Add a new bone

        :param name: New name for the bone
        :type name: str | typing.Any
        :return: Newly created edit bone
        :rtype: EditBone
        """
        ...

    def remove(self, bone: EditBone):
        """Remove an existing bone from the armature

        :param bone: EditBone to remove
        :type bone: EditBone
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
