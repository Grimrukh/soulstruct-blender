import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .driver_variable import DriverVariable

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ChannelDriverVariables(bpy_prop_collection[DriverVariable], bpy_struct):
    """Collection of channel driver Variables"""

    def new(self) -> DriverVariable:
        """Add a new variable for the driver

        :return: Newly created Driver Variable
        :rtype: DriverVariable
        """
        ...

    def remove(self, variable: DriverVariable):
        """Remove an existing variable from the driver

        :param variable: Variable to remove from the driver
        :type variable: DriverVariable
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
