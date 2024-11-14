import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_thickness_modifier import LineStyleThicknessModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleThicknessModifiers(
    bpy_prop_collection[LineStyleThicknessModifier], bpy_struct
):
    """Thickness modifiers for changing line thickness"""

    def new(
        self, name: str | typing.Any, type: str | None
    ) -> LineStyleThicknessModifier:
        """Add a thickness modifier to line style

        :param name: New name for the thickness modifier (not unique)
        :type name: str | typing.Any
        :param type: Thickness modifier type to add
        :type type: str | None
        :return: Newly added thickness modifier
        :rtype: LineStyleThicknessModifier
        """
        ...

    def remove(self, modifier: LineStyleThicknessModifier):
        """Remove a thickness modifier from line style

        :param modifier: Thickness modifier to remove
        :type modifier: LineStyleThicknessModifier
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
