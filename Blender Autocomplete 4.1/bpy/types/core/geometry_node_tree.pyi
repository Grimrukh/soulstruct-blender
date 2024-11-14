import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GeometryNodeTree(NodeTree, ID, bpy_struct):
    """Node tree consisting of linked nodes used for geometries"""

    is_mode_edit: bool
    """ The node group is used in edit mode

    :type: bool
    """

    is_mode_object: bool
    """ The node group is used in object mode

    :type: bool
    """

    is_mode_sculpt: bool
    """ The node group is used in sculpt mode

    :type: bool
    """

    is_modifier: bool
    """ The node group is used as a geometry modifier

    :type: bool
    """

    is_tool: bool
    """ The node group is used as a tool

    :type: bool
    """

    is_type_curve: bool
    """ The node group is used for curves

    :type: bool
    """

    is_type_mesh: bool
    """ The node group is used for meshes

    :type: bool
    """

    is_type_point_cloud: bool
    """ The node group is used for point clouds

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
