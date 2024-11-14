import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .context import Context
from .ui_layout import UILayout

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Menu(bpy_struct):
    """Editor menu containing buttons"""

    bl_description: str
    """ 

    :type: str
    """

    bl_idname: str
    """ If this is set, the menu gets a custom ID, otherwise it takes the name of the class used to define the menu (for example, if the class name is "OBJECT_MT_hello", and bl_idname is not set by the script, then bl_idname = "OBJECT_MT_hello")

    :type: str
    """

    bl_label: str
    """ The menu label

    :type: str
    """

    bl_options: set[str]
    """ Options for this menu type

    :type: set[str]
    """

    bl_owner_id: str
    """ 

    :type: str
    """

    bl_translation_context: str | typing.Any
    """ 

    :type: str | typing.Any
    """

    layout: UILayout
    """ Defines the structure of the menu in the UI

    :type: UILayout
    """

    @classmethod
    def poll(cls, context: Context | None) -> bool:
        """If this method returns a non-null output, then the menu can be drawn

        :param context:
        :type context: Context | None
        :return:
        :rtype: bool
        """
        ...

    def draw(self, context: Context | None):
        """Draw UI elements into the menu UI layout

        :param context:
        :type context: Context | None
        """
        ...

    def draw_preset(self, _context):
        """Define these on the subclass:
        - preset_operator (string)
        - preset_subdir (string)Optionally:
        - preset_add_operator (string)
        - preset_extensions (set of strings)
        - preset_operator_defaults (dict of keyword args)

                :param _context:
        """
        ...

    def path_menu(
        self,
        searchpaths: list[str] | None,
        operator: str | None,
        *,
        props_default: dict | None = None,
        prop_filepath: str | None = "filepath",
        filter_ext: collections.abc.Callable | None = None,
        filter_path=None,
        display_name: collections.abc.Callable | None = None,
        add_operator=None,
    ):
        """Populate a menu from a list of paths.

                :param searchpaths: Paths to scan.
                :type searchpaths: list[str] | None
                :param operator: The operator id to use with each file.
                :type operator: str | None
                :param props_default: Properties to assign to each operator.
                :type props_default: dict | None
                :param prop_filepath: Optional operator filepath property (defaults to "filepath").
                :type prop_filepath: str | None
                :param filter_ext: Optional callback that takes the file extensions.

        Returning false excludes the file from the list.
                :type filter_ext: collections.abc.Callable | None
                :param filter_path:
                :param display_name: Optional callback that takes the full path, returns the name to display.
                :type display_name: collections.abc.Callable | None
                :param add_operator:
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

    @classmethod
    def append(cls, draw_func):
        """

        :param draw_func:
        """
        ...

    @classmethod
    def prepend(cls, draw_func):
        """

        :param draw_func:
        """
        ...

    @classmethod
    def remove(cls, draw_func):
        """

        :param draw_func:
        """
        ...
