import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .mask_layer import MaskLayer

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaskLayers(bpy_prop_collection[MaskLayer], bpy_struct):
    """Collection of layers used by mask"""

    active: MaskLayer | None
    """ Active layer in this mask

    :type: MaskLayer | None
    """

    def new(self, name: str | typing.Any = "") -> MaskLayer:
        """Add layer to this mask

        :param name: Name, Name of new layer
        :type name: str | typing.Any
        :return: New mask layer
        :rtype: MaskLayer
        """
        ...

    def remove(self, layer: MaskLayer):
        """Remove layer from this mask

        :param layer: Shape to be removed
        :type layer: MaskLayer
        """
        ...

    def clear(self):
        """Remove all mask layers"""
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
