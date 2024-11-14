import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .ui_list import UIList

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PARTICLE_UL_particle_systems(UIList, bpy_struct):
    def draw_item(
        self,
        _context,
        layout,
        data,
        item,
        icon,
        _active_data,
        _active_propname,
        _index,
        _flt_flag,
    ):
        """

        :param _context:
        :param layout:
        :param data:
        :param item:
        :param icon:
        :param _active_data:
        :param _active_propname:
        :param _index:
        :param _flt_flag:
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
