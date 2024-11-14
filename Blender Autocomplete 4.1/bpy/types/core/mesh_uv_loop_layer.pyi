import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .float2_attribute_value import Float2AttributeValue
from .bool_attribute_value import BoolAttributeValue
from .mesh_uv_loop import MeshUVLoop

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshUVLoopLayer(bpy_struct):
    active: bool | None
    """ Set the map as active for display and editing

    :type: bool | None
    """

    active_clone: bool | None
    """ Set the map as active for cloning

    :type: bool | None
    """

    active_render: bool | None
    """ Set the UV map as active for rendering

    :type: bool | None
    """

    data: bpy_prop_collection[MeshUVLoop]
    """ Deprecated, use 'uv', 'vertex_select', 'edge_select' or 'pin' properties instead

    :type: bpy_prop_collection[MeshUVLoop]
    """

    edge_selection: bpy_prop_collection[BoolAttributeValue]
    """ Selection state of the edge in the UV editor

    :type: bpy_prop_collection[BoolAttributeValue]
    """

    name: str
    """ Name of UV map

    :type: str
    """

    pin: bpy_prop_collection[BoolAttributeValue]
    """ UV pinned state in the UV editor

    :type: bpy_prop_collection[BoolAttributeValue]
    """

    uv: bpy_prop_collection[Float2AttributeValue]
    """ UV coordinates on face corners

    :type: bpy_prop_collection[Float2AttributeValue]
    """

    vertex_selection: bpy_prop_collection[BoolAttributeValue]
    """ Selection state of the face corner the UV editor

    :type: bpy_prop_collection[BoolAttributeValue]
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
