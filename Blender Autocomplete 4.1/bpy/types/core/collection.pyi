import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .collection_object import CollectionObject
from .collection_children import CollectionChildren
from .id import ID
from .object import Object
from .collection_child import CollectionChild
from .collection_objects import CollectionObjects

if typing.TYPE_CHECKING:
    from io_soulstruct.types import SoulstructCollectionType

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Collection(ID, bpy_struct):
    """Collection of Object data-blocks"""

    # CUSTOM SOULSTRUCT PROPERTIES
    soulstruct_type: SoulstructCollectionType

    all_objects: bpy_prop_collection[Object]
    """ Objects that are in this collection and its child collections

    :type: bpy_prop_collection[Object]
    """

    children: CollectionChildren
    """ Collections that are immediate children of this collection

    :type: CollectionChildren
    """

    collection_children: bpy_prop_collection[CollectionChild]
    """ Children collections their parent-collection-specific settings

    :type: bpy_prop_collection[CollectionChild]
    """

    collection_objects: bpy_prop_collection[CollectionObject]
    """ Objects of the collection with their parent-collection-specific settings

    :type: bpy_prop_collection[CollectionObject]
    """

    color_tag: str
    """ Color tag for a collection

    :type: str
    """

    hide_render: bool
    """ Globally disable in renders

    :type: bool
    """

    hide_select: bool
    """ Disable selection in viewport

    :type: bool
    """

    hide_viewport: bool
    """ Globally disable in viewports

    :type: bool
    """

    instance_offset: mathutils.Vector
    """ Offset from the origin to use when instancing

    :type: mathutils.Vector
    """

    lineart_intersection_mask: list[bool]
    """ Intersection generated by this collection will have this mask value

    :type: list[bool]
    """

    lineart_intersection_priority: int
    """ The intersection line will be included into the object with the higher intersection priority value

    :type: int
    """

    lineart_usage: str
    """ How to use this collection in line art

    :type: str
    """

    lineart_use_intersection_mask: bool
    """ Use custom intersection mask for faces in this collection

    :type: bool
    """

    objects: CollectionObjects
    """ Objects that are directly in this collection

    :type: CollectionObjects
    """

    use_lineart_intersection_priority: bool
    """ Assign intersection priority value for this collection

    :type: bool
    """

    children_recursive: typing.Any
    """ A list of all children from this collection.(readonly)"""

    users_dupli_group: typing.Any
    """ The collection instance objects this collection is used in(readonly)"""

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
