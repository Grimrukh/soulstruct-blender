import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .view_layer import ViewLayer

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ViewLayers(bpy_prop_collection[ViewLayer], bpy_struct):
    """Collection of render layers"""

    def new(self, name: str | typing.Any) -> ViewLayer:
        """Add a view layer to scene

        :param name: New name for the view layer (not unique)
        :type name: str | typing.Any
        :return: Newly created view layer
        :rtype: ViewLayer
        """
        ...

    def remove(self, layer: ViewLayer):
        """Remove a view layer

        :param layer: View layer to remove
        :type layer: ViewLayer
        """
        ...

    def move(self, from_index: int | None, to_index: int | None):
        """Move a view layer

        :param from_index: From Index, Index to move
        :type from_index: int | None
        :param to_index: To Index, Target index
        :type to_index: int | None
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
