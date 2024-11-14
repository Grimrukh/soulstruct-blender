import typing
import collections.abc
import mathutils
from .theme_collection_color import ThemeCollectionColor
from .theme_view3_d import ThemeView3D
from .theme_bone_color_set import ThemeBoneColorSet
from .theme_nla_editor import ThemeNLAEditor
from .theme_strip_color import ThemeStripColor
from .theme_clip_editor import ThemeClipEditor
from .theme_file_browser import ThemeFileBrowser
from .struct import Struct
from .theme_spreadsheet import ThemeSpreadsheet
from .theme_info import ThemeInfo
from .theme_text_editor import ThemeTextEditor
from .theme_image_editor import ThemeImageEditor
from .theme_sequence_editor import ThemeSequenceEditor
from .theme_graph_editor import ThemeGraphEditor
from .bpy_prop_collection import bpy_prop_collection
from .theme_status_bar import ThemeStatusBar
from .theme_node_editor import ThemeNodeEditor
from .theme_preferences import ThemePreferences
from .theme_user_interface import ThemeUserInterface
from .theme_top_bar import ThemeTopBar
from .theme_outliner import ThemeOutliner
from .theme_dope_sheet import ThemeDopeSheet
from .theme_properties import ThemeProperties
from .bpy_struct import bpy_struct
from .theme_console import ThemeConsole

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Theme(bpy_struct):
    """User interface styling and color settings"""

    bone_color_sets: bpy_prop_collection[ThemeBoneColorSet]
    """ 

    :type: bpy_prop_collection[ThemeBoneColorSet]
    """

    clip_editor: ThemeClipEditor
    """ 

    :type: ThemeClipEditor
    """

    collection_color: bpy_prop_collection[ThemeCollectionColor]
    """ 

    :type: bpy_prop_collection[ThemeCollectionColor]
    """

    console: ThemeConsole
    """ 

    :type: ThemeConsole
    """

    dopesheet_editor: ThemeDopeSheet
    """ 

    :type: ThemeDopeSheet
    """

    file_browser: ThemeFileBrowser
    """ 

    :type: ThemeFileBrowser
    """

    graph_editor: ThemeGraphEditor
    """ 

    :type: ThemeGraphEditor
    """

    image_editor: ThemeImageEditor
    """ 

    :type: ThemeImageEditor
    """

    info: ThemeInfo
    """ 

    :type: ThemeInfo
    """

    name: str
    """ Name of the theme

    :type: str
    """

    nla_editor: ThemeNLAEditor
    """ 

    :type: ThemeNLAEditor
    """

    node_editor: ThemeNodeEditor
    """ 

    :type: ThemeNodeEditor
    """

    outliner: ThemeOutliner
    """ 

    :type: ThemeOutliner
    """

    preferences: ThemePreferences
    """ 

    :type: ThemePreferences
    """

    properties: ThemeProperties
    """ 

    :type: ThemeProperties
    """

    sequence_editor: ThemeSequenceEditor
    """ 

    :type: ThemeSequenceEditor
    """

    spreadsheet: ThemeSpreadsheet
    """ 

    :type: ThemeSpreadsheet
    """

    statusbar: ThemeStatusBar
    """ 

    :type: ThemeStatusBar
    """

    strip_color: bpy_prop_collection[ThemeStripColor]
    """ 

    :type: bpy_prop_collection[ThemeStripColor]
    """

    text_editor: ThemeTextEditor
    """ 

    :type: ThemeTextEditor
    """

    theme_area: str
    """ 

    :type: str
    """

    topbar: ThemeTopBar
    """ 

    :type: ThemeTopBar
    """

    user_interface: ThemeUserInterface
    """ 

    :type: ThemeUserInterface
    """

    view_3d: ThemeView3D
    """ 

    :type: ThemeView3D
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
