import typing
import collections.abc
import mathutils
from .node_enum_definition_items import NodeEnumDefinitionItems
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_enum_item import NodeEnumItem

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeEnumDefinition(bpy_struct):
    """Definition of an enumeration for nodes"""

    active_index: int | None
    """ Index of the active item

    :type: int | None
    """

    active_item: NodeEnumItem | None
    """ Active item

    :type: NodeEnumItem | None
    """

    enum_items: NodeEnumDefinitionItems
    """ 

    :type: NodeEnumDefinitionItems
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
