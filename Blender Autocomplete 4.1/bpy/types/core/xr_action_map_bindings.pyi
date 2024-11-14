import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .xr_action_map_binding import XrActionMapBinding
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrActionMapBindings(bpy_prop_collection[XrActionMapBinding], bpy_struct):
    """Collection of XR action map bindings"""

    def new(
        self, name: str | typing.Any, replace_existing: bool | None
    ) -> XrActionMapBinding:
        """new

        :param name: Name of the action map binding
        :type name: str | typing.Any
        :param replace_existing: Replace Existing, Replace any existing binding with the same name
        :type replace_existing: bool | None
        :return: Binding, Added action map binding
        :rtype: XrActionMapBinding
        """
        ...

    def new_from_binding(self, binding: XrActionMapBinding) -> XrActionMapBinding:
        """new_from_binding

        :param binding: Binding, Binding to use as a reference
        :type binding: XrActionMapBinding
        :return: Binding, Added action map binding
        :rtype: XrActionMapBinding
        """
        ...

    def remove(self, binding: XrActionMapBinding):
        """remove

        :param binding: Binding
        :type binding: XrActionMapBinding
        """
        ...

    def find(self, name: str | typing.Any) -> XrActionMapBinding:
        """find

        :param name: Name
        :type name: str | typing.Any
        :return: Binding, The action map binding with the given name
        :rtype: XrActionMapBinding
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
