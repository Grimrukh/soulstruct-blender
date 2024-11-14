import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .ui_layout import UILayout

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AddonPreferences(bpy_struct):
    bl_idname: str
    """ 

    :type: str
    """

    layout: UILayout
    """ 

    :type: UILayout
    """

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
