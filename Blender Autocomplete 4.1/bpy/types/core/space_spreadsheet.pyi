import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .space import Space
from .struct import Struct
from .viewer_path import ViewerPath
from .bpy_struct import bpy_struct
from .spreadsheet_row_filter import SpreadsheetRowFilter
from .spreadsheet_column import SpreadsheetColumn

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceSpreadsheet(Space, bpy_struct):
    """Spreadsheet space data"""

    attribute_domain: str
    """ Attribute domain to display

    :type: str
    """

    columns: bpy_prop_collection[SpreadsheetColumn]
    """ Persistent data associated with spreadsheet columns

    :type: bpy_prop_collection[SpreadsheetColumn]
    """

    display_viewer_path_collapsed: bool
    """ 

    :type: bool
    """

    geometry_component_type: str
    """ Part of the geometry to display data from

    :type: str
    """

    is_pinned: bool
    """ Context path is pinned

    :type: bool
    """

    object_eval_state: str
    """ 

    :type: str
    """

    row_filters: bpy_prop_collection[SpreadsheetRowFilter]
    """ Filters to remove rows from the displayed data

    :type: bpy_prop_collection[SpreadsheetRowFilter]
    """

    show_only_selected: bool
    """ Only include rows that correspond to selected elements

    :type: bool
    """

    show_region_channels: bool
    """ 

    :type: bool
    """

    show_region_footer: bool
    """ 

    :type: bool
    """

    show_region_toolbar: bool
    """ 

    :type: bool
    """

    show_region_ui: bool
    """ 

    :type: bool
    """

    use_filter: bool
    """ 

    :type: bool
    """

    viewer_path: ViewerPath
    """ Path to the data that is displayed in the spreadsheet

    :type: ViewerPath
    """

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

    @classmethod
    def draw_handler_add(
        cls,
        callback: typing.Any | None,
        args: tuple | None,
        region_type: str | None,
        draw_type: str | None,
    ) -> typing.Any:
        """Add a new draw handler to this space type.
        It will be called every time the specified region in the space type will be drawn.
        Note: All arguments are positional only for now.

                :param callback: A function that will be called when the region is drawn.
        It gets the specified arguments as input.
                :type callback: typing.Any | None
                :param args: Arguments that will be passed to the callback.
                :type args: tuple | None
                :param region_type: The region type the callback draws in; usually WINDOW. (`bpy.types.Region.type`)
                :type region_type: str | None
                :param draw_type: Usually POST_PIXEL for 2D drawing and POST_VIEW for 3D drawing. In some cases PRE_VIEW can be used. BACKDROP can be used for backdrops in the node editor.
                :type draw_type: str | None
                :return: Handler that can be removed later on.
                :rtype: typing.Any
        """
        ...

    @classmethod
    def draw_handler_remove(cls, handler: typing.Any | None, region_type: str | None):
        """Remove a draw handler that was added previously.

        :param handler: The draw handler that should be removed.
        :type handler: typing.Any | None
        :param region_type: Region type the callback was added to.
        :type region_type: str | None
        """
        ...
