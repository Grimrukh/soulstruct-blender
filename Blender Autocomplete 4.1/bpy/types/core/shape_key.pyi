import typing
import collections.abc
import mathutils
from .unknown_type import UnknownType
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .shape_key_point import ShapeKeyPoint

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShapeKey(bpy_struct):
    """Shape key in a shape keys data-block"""

    data: bpy_prop_collection[UnknownType]
    """ 

    :type: bpy_prop_collection[UnknownType]
    """

    frame: float
    """ Frame for absolute keys

    :type: float
    """

    interpolation: str
    """ Interpolation type for absolute shape keys

    :type: str
    """

    lock_shape: bool
    """ Protect the shape key from accidental sculpting and editing

    :type: bool
    """

    mute: bool
    """ Toggle this shape key

    :type: bool
    """

    name: str
    """ Name of Shape Key

    :type: str
    """

    points: bpy_prop_collection[ShapeKeyPoint]
    """ Optimized access to shape keys point data, when using foreach_get/foreach_set accessors. (Warning: Does not support legacy Curve shape keys)

    :type: bpy_prop_collection[ShapeKeyPoint]
    """

    relative_key: ShapeKey
    """ Shape used as a relative key

    :type: ShapeKey
    """

    slider_max: float
    """ Maximum for slider

    :type: float
    """

    slider_min: float
    """ Minimum for slider

    :type: float
    """

    value: float
    """ Value of shape key at the current frame

    :type: float
    """

    vertex_group: str
    """ Vertex weight group, to blend with basis shape

    :type: str
    """

    def normals_vertex_get(self) -> float:
        """Compute local space vertices' normals for this shape key

        :return: normals
        :rtype: float
        """
        ...

    def normals_polygon_get(self) -> float:
        """Compute local space faces' normals for this shape key

        :return: normals
        :rtype: float
        """
        ...

    def normals_split_get(self) -> float:
        """Compute local space face corners' normals for this shape key

        :return: normals
        :rtype: float
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
