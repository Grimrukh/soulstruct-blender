import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .mask_spline_point import MaskSplinePoint
from .mask_spline import MaskSpline

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaskSplines(bpy_prop_collection[MaskSpline], bpy_struct):
    """Collection of masking splines"""

    active: MaskSpline | None
    """ Active spline of masking layer

    :type: MaskSpline | None
    """

    active_point: MaskSplinePoint | None
    """ Active point of masking layer

    :type: MaskSplinePoint | None
    """

    def new(self) -> MaskSpline:
        """Add a new spline to the layer

        :return: The newly created spline
        :rtype: MaskSpline
        """
        ...

    def remove(self, spline: MaskSpline):
        """Remove a spline from a layer

        :param spline: The spline to remove
        :type spline: MaskSpline
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
