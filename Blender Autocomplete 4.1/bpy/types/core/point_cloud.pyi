import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .point import Point
from .bpy_struct import bpy_struct
from .attribute_group import AttributeGroup
from .anim_data import AnimData
from .id import ID
from .id_materials import IDMaterials

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PointCloud(ID, bpy_struct):
    """Point cloud data-block"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    attributes: AttributeGroup
    """ Geometry attributes

    :type: AttributeGroup
    """

    color_attributes: AttributeGroup
    """ Geometry color attributes

    :type: AttributeGroup
    """

    materials: IDMaterials
    """ 

    :type: IDMaterials
    """

    points: bpy_prop_collection[Point]
    """ 

    :type: bpy_prop_collection[Point]
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
