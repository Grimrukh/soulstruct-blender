import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .line_style_color_modifier import LineStyleColorModifier
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleColorModifiers(bpy_prop_collection[LineStyleColorModifier], bpy_struct):
    """Color modifiers for changing line colors"""

    def new(self, name: str | typing.Any, type: str | None) -> LineStyleColorModifier:
        """Add a color modifier to line style

        :param name: New name for the color modifier (not unique)
        :type name: str | typing.Any
        :param type: Color modifier type to add
        :type type: str | None
        :return: Newly added color modifier
        :rtype: LineStyleColorModifier
        """
        ...

    def remove(self, modifier: LineStyleColorModifier):
        """Remove a color modifier from line style

        :param modifier: Color modifier to remove
        :type modifier: LineStyleColorModifier
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
