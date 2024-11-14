import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GpencilModifier(bpy_struct):
    """Modifier affecting the Grease Pencil object"""

    is_override_data: bool
    """ In a local override object, whether this modifier comes from the linked reference object, or is local to the override

    :type: bool
    """

    name: str
    """ Modifier name

    :type: str
    """

    show_expanded: bool
    """ Set modifier expanded in the user interface

    :type: bool
    """

    show_in_editmode: bool
    """ Display modifier in Edit mode

    :type: bool
    """

    show_render: bool
    """ Use modifier during render

    :type: bool
    """

    show_viewport: bool
    """ Display modifier in viewport

    :type: bool
    """

    type: str
    """ 

    :type: str
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
