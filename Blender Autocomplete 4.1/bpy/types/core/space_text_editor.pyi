import typing
import collections.abc
import mathutils
from .space import Space
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .text import Text

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceTextEditor(Space, bpy_struct):
    """Text editor space data"""

    find_text: str
    """ Text to search for with the find tool

    :type: str
    """

    font_size: int
    """ Font size to use for displaying the text

    :type: int
    """

    margin_column: int
    """ Column number to show right margin at

    :type: int
    """

    replace_text: str
    """ Text to replace selected text with using the replace tool

    :type: str
    """

    show_line_highlight: bool
    """ Highlight the current line

    :type: bool
    """

    show_line_numbers: bool
    """ Show line numbers next to the text

    :type: bool
    """

    show_margin: bool
    """ Show right margin

    :type: bool
    """

    show_region_footer: bool
    """ 

    :type: bool
    """

    show_region_ui: bool
    """ 

    :type: bool
    """

    show_syntax_highlight: bool
    """ Syntax highlight for scripting

    :type: bool
    """

    show_word_wrap: bool
    """ Wrap words if there is not enough horizontal space

    :type: bool
    """

    tab_width: int
    """ Number of spaces to display tabs with

    :type: int
    """

    text: Text
    """ Text displayed and edited in this space

    :type: Text
    """

    top: int
    """ Top line visible

    :type: int
    """

    use_find_all: bool
    """ Search in all text data-blocks, instead of only the active one

    :type: bool
    """

    use_find_wrap: bool
    """ Search again from the start of the file when reaching the end

    :type: bool
    """

    use_live_edit: bool
    """ Run Python while editing

    :type: bool
    """

    use_match_case: bool
    """ Search string is sensitive to uppercase and lowercase letters

    :type: bool
    """

    use_overwrite: bool
    """ Overwrite characters when typing rather than inserting them

    :type: bool
    """

    visible_lines: int
    """ Amount of lines that can be visible in current editor

    :type: int
    """

    def is_syntax_highlight_supported(self) -> bool:
        """Returns True if the editor supports syntax highlighting for the current text datablock

        :return:
        :rtype: bool
        """
        ...

    def region_location_from_cursor(
        self, line: int | None, column: int | None
    ) -> bpy_prop_array[int]:
        """Retrieve the region position from the given line and character position

        :param line: Line, Line index
        :type line: int | None
        :param column: Column, Column index
        :type column: int | None
        :return: Region coordinates
        :rtype: bpy_prop_array[int]
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
