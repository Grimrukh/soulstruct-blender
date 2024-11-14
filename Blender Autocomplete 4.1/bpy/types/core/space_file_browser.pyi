import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .file_browser_fs_menu_entry import FileBrowserFSMenuEntry
from .space import Space
from .struct import Struct
from .file_select_params import FileSelectParams
from .bpy_struct import bpy_struct
from .operator import Operator
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceFileBrowser(Space, bpy_struct):
    """File browser space data"""

    active_operator: Operator
    """ 

    :type: Operator
    """

    bookmarks: bpy_prop_collection[FileBrowserFSMenuEntry]
    """ User's bookmarks

    :type: bpy_prop_collection[FileBrowserFSMenuEntry]
    """

    bookmarks_active: int
    """ Index of active bookmark (-1 if none)

    :type: int
    """

    browse_mode: str
    """ Type of the File Editor view (regular file browsing or asset browsing)

    :type: str
    """

    operator: Operator
    """ 

    :type: Operator
    """

    params: FileSelectParams
    """ Parameters and Settings for the Filebrowser

    :type: FileSelectParams
    """

    recent_folders: bpy_prop_collection[FileBrowserFSMenuEntry]
    """ 

    :type: bpy_prop_collection[FileBrowserFSMenuEntry]
    """

    recent_folders_active: int
    """ Index of active recent folder (-1 if none)

    :type: int
    """

    show_region_tool_props: bool
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

    system_bookmarks: bpy_prop_collection[FileBrowserFSMenuEntry]
    """ System's bookmarks

    :type: bpy_prop_collection[FileBrowserFSMenuEntry]
    """

    system_bookmarks_active: int
    """ Index of active system bookmark (-1 if none)

    :type: int
    """

    system_folders: bpy_prop_collection[FileBrowserFSMenuEntry]
    """ System's folders (usually root, available hard drives, etc)

    :type: bpy_prop_collection[FileBrowserFSMenuEntry]
    """

    system_folders_active: int
    """ Index of active system folder (-1 if none)

    :type: int
    """

    def activate_asset_by_id(
        self, id_to_activate: ID | None, deferred: bool | typing.Any | None = False
    ):
        """Activate and select the asset entry that represents the given ID

        :param id_to_activate: id_to_activate
        :type id_to_activate: ID | None
        :param deferred: Whether to activate the ID immediately (false) or after the file browser refreshes (true)
        :type deferred: bool | typing.Any | None
        """
        ...

    def activate_file_by_relative_path(self, relative_path: str | typing.Any = ""):
        """Set active file and add to selection based on relative path to current File Browser directory

        :param relative_path: relative_path
        :type relative_path: str | typing.Any
        """
        ...

    def deselect_all(self):
        """Deselect all files"""
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
