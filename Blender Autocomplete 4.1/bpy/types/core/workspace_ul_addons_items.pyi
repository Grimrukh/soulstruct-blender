import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .ui_list import UIList

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WORKSPACE_UL_addons_items(UIList, bpy_struct):
    def draw_item(
        self,
        context,
        layout,
        _data,
        addon,
        icon,
        _active_data,
        _active_propname,
        _index,
    ):
        """

        :param context:
        :param layout:
        :param _data:
        :param addon:
        :param icon:
        :param _active_data:
        :param _active_propname:
        :param _index:
        """
        ...

    def filter_items(self, _context, data, property):
        """

        :param _context:
        :param data:
        :param property:
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
