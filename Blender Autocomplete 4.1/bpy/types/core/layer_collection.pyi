import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .view_layer import ViewLayer

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LayerCollection(bpy_struct):
    """Layer collection"""

    children: bpy_prop_collection[LayerCollection]
    """ Layer collection children

    :type: bpy_prop_collection[LayerCollection]
    """

    collection: Collection
    """ Collection this layer collection is wrapping

    :type: Collection
    """

    exclude: bool
    """ Exclude from view layer

    :type: bool
    """

    hide_viewport: bool
    """ Temporarily hide in viewport

    :type: bool
    """

    holdout: bool
    """ Mask out objects in collection from view layer

    :type: bool
    """

    indirect_only: bool
    """ Objects in collection only contribute indirectly (through shadows and reflections) in the view layer

    :type: bool
    """

    is_visible: bool
    """ Whether this collection is visible for the view layer, take into account the collection parent

    :type: bool
    """

    name: str
    """ Name of this layer collection (same as its collection one)

    :type: str
    """

    def visible_get(self) -> bool:
        """Whether this collection is visible, take into account the collection parent and the viewport

        :return:
        :rtype: bool
        """
        ...

    def has_objects(self) -> bool:
        """

        :return:
        :rtype: bool
        """
        ...

    def has_selected_objects(self, view_layer: ViewLayer | None) -> bool:
        """

        :param view_layer: View layer the layer collection belongs to
        :type view_layer: ViewLayer | None
        :return:
        :rtype: bool
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
