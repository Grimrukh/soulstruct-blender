import typing
import collections.abc
import mathutils
from .anim_data import AnimData
from .float_vector_attribute_value import FloatVectorAttributeValue
from .struct import Struct
from .attribute_group import AttributeGroup
from .curve_point import CurvePoint
from .bpy_prop_collection import bpy_prop_collection
from .curve_slice import CurveSlice
from .object import Object
from .int_attribute_value import IntAttributeValue
from .bpy_struct import bpy_struct
from .float_vector_value_read_only import FloatVectorValueReadOnly
from .id import ID
from .id_materials import IDMaterials

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Curves(ID, bpy_struct):
    """Hair data-block for hair curves"""

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

    curve_offset_data: bpy_prop_collection[IntAttributeValue]
    """ 

    :type: bpy_prop_collection[IntAttributeValue]
    """

    curves: bpy_prop_collection[CurveSlice]
    """ All curves in the data-block

    :type: bpy_prop_collection[CurveSlice]
    """

    materials: IDMaterials
    """ 

    :type: IDMaterials
    """

    normals: bpy_prop_collection[FloatVectorValueReadOnly]
    """ The curve normal value at each of the curve's control points

    :type: bpy_prop_collection[FloatVectorValueReadOnly]
    """

    points: bpy_prop_collection[CurvePoint]
    """ Control points of all curves

    :type: bpy_prop_collection[CurvePoint]
    """

    position_data: bpy_prop_collection[FloatVectorAttributeValue]
    """ 

    :type: bpy_prop_collection[FloatVectorAttributeValue]
    """

    selection_domain: str
    """ 

    :type: str
    """

    surface: Object
    """ Mesh object that the curves can be attached to

    :type: Object
    """

    surface_uv_map: str
    """ The name of the attribute on the surface mesh used to define the attachment of each curve

    :type: str
    """

    use_mirror_x: bool
    """ Enable symmetry in the X axis

    :type: bool
    """

    use_mirror_y: bool
    """ Enable symmetry in the Y axis

    :type: bool
    """

    use_mirror_z: bool
    """ Enable symmetry in the Z axis

    :type: bool
    """

    use_sculpt_collision: bool
    """ Enable collision with the surface while sculpting

    :type: bool
    """

    def add_curves(self, sizes: collections.abc.Iterable[int] | None):
        """add_curves

        :param sizes: Sizes, The number of points in each curve
        :type sizes: collections.abc.Iterable[int] | None
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
