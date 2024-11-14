import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bone_collection import BoneCollection

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoneCollections(bpy_struct):
    """The Bone Collections of this Armature"""

    active: BoneCollection | None
    """ Armature's active bone collection

    :type: BoneCollection | None
    """

    active_index: int | None
    """ The index of the Armature's active bone collection; -1 when there is no active collection. Note that this is indexing the underlying array of bone collections, which may not be in the order you expect. Root collections are listed first, and siblings are always sequential. Apart from that, bone collections can be in any order, and thus incrementing or decrementing this index can make the active bone collection jump around in unexpected ways. For a more predictable interface, use active or active_name

    :type: int | None
    """

    active_name: str
    """ The name of the Armature's active bone collection; empty when there is no active collection

    :type: str
    """

    is_solo_active: bool
    """ Read-only flag that indicates there is at least one bone collection marked as 'solo'

    :type: bool
    """

    def new(
        self, name: str | typing.Any, parent: BoneCollection | None = None
    ) -> BoneCollection:
        """Add a new empty bone collection to the armature

        :param name: Name, Name of the new collection. Blender will ensure it is unique within the collections of the Armature
        :type name: str | typing.Any
        :param parent: Parent Collection, If not None, the new bone collection becomes a child of this collection
        :type parent: BoneCollection | None
        :return: Newly created bone collection
        :rtype: BoneCollection
        """
        ...

    def remove(self, bone_collection: BoneCollection | None):
        """Remove the bone collection from the armature. If this bone collection has any children, they will be reassigned to their grandparent; in other words, the children will take the place of the removed bone collection

        :param bone_collection: Bone Collection, The bone collection to remove
        :type bone_collection: BoneCollection | None
        """
        ...

    def move(self, from_index: int | None, to_index: int | None):
        """Move a bone collection to a different position in the collection list. This can only be used to reorder siblings, and not to change parent-child relationships

        :param from_index: From Index, Index to move
        :type from_index: int | None
        :param to_index: To Index, Target index
        :type to_index: int | None
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
