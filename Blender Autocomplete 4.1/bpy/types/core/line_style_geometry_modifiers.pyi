import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_geometry_modifier import LineStyleGeometryModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleGeometryModifiers(
    bpy_prop_collection[LineStyleGeometryModifier], bpy_struct
):
    """Geometry modifiers for changing line geometries"""

    def new(
        self, name: str | typing.Any, type: str | None
    ) -> LineStyleGeometryModifier:
        """Add a geometry modifier to line style

        :param name: New name for the geometry modifier (not unique)
        :type name: str | typing.Any
        :param type: Geometry modifier type to add
        :type type: str | None
        :return: Newly added geometry modifier
        :rtype: LineStyleGeometryModifier
        """
        ...

    def remove(self, modifier: LineStyleGeometryModifier):
        """Remove a geometry modifier from line style

        :param modifier: Geometry modifier to remove
        :type modifier: LineStyleGeometryModifier
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
