import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .ui_list import UIList

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UI_UL_list(UIList, bpy_struct):
    @staticmethod
    def filter_items_by_name(
        pattern, bitflag, items, propname="name", flags=None, reverse=False
    ):
        """Set FILTER_ITEM for items which name matches filter_name one (case-insensitive).
        pattern is the filtering pattern.
        propname is the name of the string property to use for filtering.
        flags must be a list of integers the same length as items, or None!
        return a list of flags (based on given flags if not None),
        or an empty list if no flags were given and no filtering has been done.

                :param pattern:
                :param bitflag:
                :param items:
                :param propname:
                :param flags:
                :param reverse:
        """
        ...

    @staticmethod
    def sort_items_helper(sort_data, key, reverse=False):
        """Common sorting utility. Returns a neworder list mapping org_idx -> new_idx.
        sort_data must be an (unordered) list of tuples [(org_idx, ...), (org_idx, ...), ...].
        key must be the same kind of callable you would use for sorted() builtin function.
        reverse will reverse the sorting!

                :param sort_data:
                :param key:
                :param reverse:
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
