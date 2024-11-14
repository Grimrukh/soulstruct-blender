import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .f_curve import FCurve
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ActionFCurves(bpy_prop_collection[FCurve], bpy_struct):
    """Collection of action F-Curves"""

    def new(
        self,
        data_path: str | typing.Any,
        index: typing.Any | None = 0,
        action_group: str | typing.Any = "",
    ) -> FCurve:
        """Add an F-Curve to the action

        :param data_path: Data Path, F-Curve data path to use
        :type data_path: str | typing.Any
        :param index: Index, Array index
        :type index: typing.Any | None
        :param action_group: Action Group, Acton group to add this F-Curve into
        :type action_group: str | typing.Any
        :return: Newly created F-Curve
        :rtype: FCurve
        """
        ...

    def find(self, data_path: str | typing.Any, index: typing.Any | None = 0) -> FCurve:
        """Find an F-Curve. Note that this function performs a linear scan of all F-Curves in the action.

        :param data_path: Data Path, F-Curve data path
        :type data_path: str | typing.Any
        :param index: Index, Array index
        :type index: typing.Any | None
        :return: The found F-Curve, or None if it doesn't exist
        :rtype: FCurve
        """
        ...

    def remove(self, fcurve: FCurve):
        """Remove F-Curve

        :param fcurve: F-Curve to remove
        :type fcurve: FCurve
        """
        ...

    def clear(self):
        """Remove all F-Curves"""
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
