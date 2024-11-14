import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class View2D(bpy_struct):
    """Scroll and zoom for a 2D region"""

    def region_to_view(self, x: float | None, y: float | None) -> bpy_prop_array[float]:
        """Transform region coordinates to 2D view

        :param x: x, Region x coordinate
        :type x: float | None
        :param y: y, Region y coordinate
        :type y: float | None
        :return: Result, View coordinates
        :rtype: bpy_prop_array[float]
        """
        ...

    def view_to_region(
        self, x: float | None, y: float | None, clip: bool | typing.Any | None = True
    ) -> bpy_prop_array[int]:
        """Transform 2D view coordinates to region

        :param x: x, 2D View x coordinate
        :type x: float | None
        :param y: y, 2D View y coordinate
        :type y: float | None
        :param clip: Clip, Clip coordinates to the visible region
        :type clip: bool | typing.Any | None
        :return: Result, Region coordinates
        :rtype: bpy_prop_array[int]
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
