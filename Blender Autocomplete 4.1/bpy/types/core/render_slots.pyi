import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .render_slot import RenderSlot

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RenderSlots(bpy_prop_collection[RenderSlot], bpy_struct):
    """Collection of render layers"""

    active: RenderSlot | None
    """ Active render slot of the image

    :type: RenderSlot | None
    """

    active_index: int | None
    """ Active render slot of the image

    :type: int | None
    """

    def new(self, name: str | typing.Any = "") -> RenderSlot:
        """Add a render slot to the image

        :param name: Name, New name for the render slot
        :type name: str | typing.Any
        :return: Newly created render layer
        :rtype: RenderSlot
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
