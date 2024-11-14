import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .context import Context
from .ui_layout import UILayout

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UIList(bpy_struct):
    """UI list containing the elements of a collection"""

    bitflag_filter_item: int
    """ The value of the reserved bitflag 'FILTER_ITEM' (in filter_flags values)

    :type: int
    """

    bl_idname: str
    """ If this is set, the uilist gets a custom ID, otherwise it takes the name of the class used to define the uilist (for example, if the class name is "OBJECT_UL_vgroups", and bl_idname is not set by the script, then bl_idname = "OBJECT_UL_vgroups")

    :type: str
    """

    filter_name: str
    """ Only show items matching this name (use '*' as wildcard)

    :type: str
    """

    layout_type: str
    """ 

    :type: str
    """

    list_id: str
    """ Identifier of the list, if any was passed to the "list_id" parameter of "template_list()"

    :type: str
    """

    use_filter_invert: bool
    """ Invert filtering (show hidden items, and vice versa)

    :type: bool
    """

    use_filter_show: bool
    """ Show filtering options

    :type: bool
    """

    use_filter_sort_alpha: bool
    """ Sort items by their name

    :type: bool
    """

    use_filter_sort_lock: bool
    """ Lock the order of shown items (user cannot change it)

    :type: bool
    """

    use_filter_sort_reverse: bool
    """ Reverse the order of shown items

    :type: bool
    """

    def draw_item(
        self,
        context: Context | None,
        layout: UILayout,
        data: typing.Any | None,
        item: typing.Any | None,
        icon: int | None,
        active_data: typing.Any,
        active_property: str | None,
        index: typing.Any | None = 0,
        flt_flag: typing.Any | None = 0,
    ):
        """Draw an item in the list (NOTE: when you define your own draw_item function, you may want to check given 'item' is of the right type...)

        :param context:
        :type context: Context | None
        :param layout: Layout to draw the item
        :type layout: UILayout
        :param data: Data from which to take Collection property
        :type data: typing.Any | None
        :param item: Item of the collection property
        :type item: typing.Any | None
        :param icon: Icon of the item in the collection
        :type icon: int | None
        :param active_data: Data from which to take property for the active element
        :type active_data: typing.Any
        :param active_property: Identifier of property in active_data, for the active element
        :type active_property: str | None
        :param index: Index of the item in the collection
        :type index: typing.Any | None
        :param flt_flag: The filter-flag result for this item
        :type flt_flag: typing.Any | None
        """
        ...

    def draw_filter(self, context: Context | None, layout: UILayout):
        """Draw filtering options

        :param context:
        :type context: Context | None
        :param layout: Layout to draw the item
        :type layout: UILayout
        """
        ...

    def filter_items(
        self,
        context: Context | None,
        data: typing.Any | None,
        property: str | typing.Any,
    ):
        """Filter and/or re-order items of the collection (output filter results in filter_flags, and reorder results in filter_neworder arrays)

                :param context:
                :type context: Context | None
                :param data: Data from which to take Collection property
                :type data: typing.Any | None
                :param property: Identifier of property in data, for the collection
                :type property: str | typing.Any
                :return: filter_flags, An array of filter flags, one for each item in the collection (NOTE: The upper 16 bits, including FILTER_ITEM, are reserved, only use the lower 16 bits for custom usages), int array of 1 items in [0, inf]

        filter_neworder, An array of indices, one for each item in the collection, mapping the org index to the new one, int array of 1 items in [0, inf]
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
