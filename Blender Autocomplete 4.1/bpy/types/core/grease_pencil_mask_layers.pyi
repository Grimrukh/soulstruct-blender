import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .g_pencil_layer import GPencilLayer
from .g_pencil_layer_mask import GPencilLayerMask

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GreasePencilMaskLayers(bpy_prop_collection[GPencilLayerMask], bpy_struct):
    """Collection of grease pencil masking layers"""

    active_mask_index: int | None
    """ Active index in layer mask array

    :type: int | None
    """

    def add(self, layer: GPencilLayer):
        """Add a layer to mask list

        :param layer: Layer to add as mask
        :type layer: GPencilLayer
        """
        ...

    def remove(self, mask: GPencilLayerMask):
        """Remove a layer from mask list

        :param mask: Mask to remove
        :type mask: GPencilLayerMask
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
