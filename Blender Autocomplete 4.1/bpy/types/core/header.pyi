import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .context import Context
from .ui_layout import UILayout

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Header(bpy_struct):
    """Editor header containing UI elements"""

    bl_idname: str
    """ If this is set, the header gets a custom ID, otherwise it takes the name of the class used to define the header; for example, if the class name is "OBJECT_HT_hello", and bl_idname is not set by the script, then bl_idname = "OBJECT_HT_hello"

    :type: str
    """

    bl_region_type: str
    """ The region where the header is going to be used in (defaults to header region)

    :type: str
    """

    bl_space_type: str
    """ The space where the header is going to be used in

    :type: str
    """

    layout: UILayout
    """ Structure of the header in the UI

    :type: UILayout
    """

    def draw(self, context: Context | None):
        """Draw UI elements into the header UI layout

        :param context:
        :type context: Context | None
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
