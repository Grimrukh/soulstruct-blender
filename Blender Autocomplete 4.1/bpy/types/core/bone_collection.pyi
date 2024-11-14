import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .bone import Bone

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoneCollection(bpy_struct):
    """Bone collection in an Armature data-block"""

    bones: bpy_prop_collection[Bone]
    """ Bones assigned to this bone collection. In armature edit mode this will always return an empty list of bones, as the bone collection memberships are only synchronized when exiting edit mode

    :type: bpy_prop_collection[Bone]
    """

    child_number: int
    """ Index of this collection into its parent's list of children. Note that finding this index requires a scan of all the bone collections, so do access this with care

    :type: int
    """

    children: bpy_prop_collection[BoneCollection]
    """ 

    :type: bpy_prop_collection[BoneCollection]
    """

    index: int
    """ Index of this bone collection in the armature.collections_all array. Note that finding this index requires a scan of all the bone collections, so do access this with care

    :type: int
    """

    is_editable: bool
    """ This collection is owned by a local Armature, or was added via a library override in the current blend file

    :type: bool
    """

    is_expanded: bool
    """ This bone collection is expanded in the bone collections tree view

    :type: bool
    """

    is_local_override: bool
    """ This collection was added via a library override in the current blend file

    :type: bool
    """

    is_solo: bool
    """ Show only this bone collection, and others also marked as 'solo'

    :type: bool
    """

    is_visible: bool
    """ Bones in this collection will be visible in pose/object mode

    :type: bool
    """

    is_visible_ancestors: bool
    """ True when all of the ancestors of this bone collection are marked as visible; always True for root bone collections

    :type: bool
    """

    is_visible_effectively: bool
    """ Whether this bone collection is effectively visible in the viewport. This is True when this bone collection and all of its ancestors are visible, or when it is marked as 'solo'

    :type: bool
    """

    name: str
    """ Unique within the Armature

    :type: str
    """

    parent: BoneCollection
    """ Parent bone collection. Note that accessing this requires a scan of all the bone collections to find the parent

    :type: BoneCollection
    """

    bones_recursive: typing.Any
    """ A set of all bones assigned to this bone collection and its child collections.(readonly)"""

    def assign(self, bone: typing.Any | None) -> bool:
        """Assign the given bone to this collection

        :param bone: Bone to assign to this collection. This must be a Bone, PoseBone, or EditBone
        :type bone: typing.Any | None
        :return: Assigned, Whether the bone was actually assigned; will be false if the bone was already member of the collection
        :rtype: bool
        """
        ...

    def unassign(self, bone: typing.Any | None) -> bool:
        """Remove the given bone from this collection

        :param bone: Bone to remove from this collection. This must be a Bone, PoseBone, or EditBone
        :type bone: typing.Any | None
        :return: Unassigned, Whether the bone was actually removed; will be false if the bone was not a member of the collection to begin with
        :rtype: bool
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
