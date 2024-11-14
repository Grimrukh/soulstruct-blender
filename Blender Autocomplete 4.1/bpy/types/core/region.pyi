import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .view2_d import View2D

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Region(bpy_struct):
    """Region in a subdivided screen area"""

    active_panel_category: str | None
    """ The current active panel category, may be Null if the region does not support this feature (NOTE: these categories are generated at runtime, so list may be empty at initialization, before any drawing took place)

    :type: str | None
    """

    alignment: str
    """ Alignment of the region within the area

    :type: str
    """

    data: typing.Any
    """ Region specific data (the type depends on the region type)

    :type: typing.Any
    """

    height: int
    """ Region height

    :type: int
    """

    type: str
    """ Type of this region

    :type: str
    """

    view2d: View2D
    """ 2D view of the region

    :type: View2D
    """

    width: int
    """ Region width

    :type: int
    """

    x: int
    """ The window relative vertical location of the region

    :type: int
    """

    y: int
    """ The window relative horizontal location of the region

    :type: int
    """

    def tag_redraw(self):
        """tag_redraw"""
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
