import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .f_curve import FCurve
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AnimDataDrivers(bpy_prop_collection[FCurve], bpy_struct):
    """Collection of Driver F-Curves"""

    def new(self, data_path: str | typing.Any, index: typing.Any | None = 0) -> FCurve:
        """new

        :param data_path: Data Path, F-Curve data path to use
        :type data_path: str | typing.Any
        :param index: Index, Array index
        :type index: typing.Any | None
        :return: Newly Driver F-Curve
        :rtype: FCurve
        """
        ...

    def remove(self, driver: FCurve):
        """remove

        :param driver:
        :type driver: FCurve
        """
        ...

    def from_existing(self, src_driver: FCurve | None = None) -> FCurve:
        """Add a new driver given an existing one

        :param src_driver: Existing Driver F-Curve to use as template for a new one
        :type src_driver: FCurve | None
        :return: New Driver F-Curve
        :rtype: FCurve
        """
        ...

    def find(self, data_path: str | typing.Any, index: typing.Any | None = 0) -> FCurve:
        """Find a driver F-Curve. Note that this function performs a linear scan of all driver F-Curves.

        :param data_path: Data Path, F-Curve data path
        :type data_path: str | typing.Any
        :param index: Index, Array index
        :type index: typing.Any | None
        :return: The found F-Curve, or None if it doesn't exist
        :rtype: FCurve
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
