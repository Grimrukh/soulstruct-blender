import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .region import Region
from .struct import Struct
from .bpy_struct import bpy_struct
from .area_spaces import AreaSpaces

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Area(bpy_struct):
    """Area in a subdivided screen, containing an editor"""

    height: int
    """ Area height

    :type: int
    """

    regions: bpy_prop_collection[Region]
    """ Regions this area is subdivided in

    :type: bpy_prop_collection[Region]
    """

    show_menus: bool
    """ Show menus in the header

    :type: bool
    """

    spaces: AreaSpaces
    """ Spaces contained in this area, the first being the active space (NOTE: Useful for example to restore a previously used 3D view space in a certain area to get the old view orientation)

    :type: AreaSpaces
    """

    type: str
    """ Current editor type for this area

    :type: str
    """

    ui_type: str
    """ Current editor type for this area

    :type: str
    """

    width: int
    """ Area width

    :type: int
    """

    x: int
    """ The window relative vertical location of the area

    :type: int
    """

    y: int
    """ The window relative horizontal location of the area

    :type: int
    """

    def tag_redraw(self):
        """tag_redraw"""
        ...

    def header_text_set(self, text: str | None):
        """Set the header status text

        :param text: Text, New string for the header, None clears the text
        :type text: str | None
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
