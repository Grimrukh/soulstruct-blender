import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_alpha_modifier import LineStyleAlphaModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleAlphaModifiers(bpy_prop_collection[LineStyleAlphaModifier], bpy_struct):
    """Alpha modifiers for changing line alphas"""

    def new(self, name: str | typing.Any, type: str | None) -> LineStyleAlphaModifier:
        """Add a alpha modifier to line style

        :param name: New name for the alpha modifier (not unique)
        :type name: str | typing.Any
        :param type: Alpha modifier type to add
        :type type: str | None
        :return: Newly added alpha modifier
        :rtype: LineStyleAlphaModifier
        """
        ...

    def remove(self, modifier: LineStyleAlphaModifier):
        """Remove a alpha modifier from line style

        :param modifier: Alpha modifier to remove
        :type modifier: LineStyleAlphaModifier
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
