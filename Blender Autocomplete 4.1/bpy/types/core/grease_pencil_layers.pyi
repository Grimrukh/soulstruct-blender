import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .g_pencil_layer import GPencilLayer

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GreasePencilLayers(bpy_prop_collection[GPencilLayer], bpy_struct):
    """Collection of grease pencil layers"""

    active: GPencilLayer | None
    """ Active grease pencil layer

    :type: GPencilLayer | None
    """

    active_index: int | None
    """ Index of active grease pencil layer

    :type: int | None
    """

    active_note: str | None
    """ Note/Layer to add annotation strokes to

    :type: str | None
    """

    def new(
        self, name: str | typing.Any, set_active: bool | typing.Any | None = True
    ) -> GPencilLayer:
        """Add a new grease pencil layer

        :param name: Name, Name of the layer
        :type name: str | typing.Any
        :param set_active: Set Active, Set the newly created layer to the active layer
        :type set_active: bool | typing.Any | None
        :return: The newly created layer
        :rtype: GPencilLayer
        """
        ...

    def remove(self, layer: GPencilLayer):
        """Remove a grease pencil layer

        :param layer: The layer to remove
        :type layer: GPencilLayer
        """
        ...

    def move(self, layer: GPencilLayer, type: str | None):
        """Move a grease pencil layer in the layer stack

        :param layer: The layer to move
        :type layer: GPencilLayer
        :param type: Direction of movement
        :type type: str | None
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
