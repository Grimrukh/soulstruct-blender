import typing
import collections.abc
import mathutils
from .text_line import TextLine
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Text(ID, bpy_struct):
    """Text data-block referencing an external or packed text file"""

    current_character: int
    """ Index of current character in current line, and also start index of character in selection if one exists

    :type: int
    """

    current_line: TextLine
    """ Current line, and start line of selection if one exists

    :type: TextLine
    """

    current_line_index: int
    """ Index of current TextLine in TextLine collection

    :type: int
    """

    filepath: str
    """ Filename of the text file

    :type: str
    """

    indentation: str
    """ Use tabs or spaces for indentation

    :type: str
    """

    is_dirty: bool
    """ Text file has been edited since last save

    :type: bool
    """

    is_in_memory: bool
    """ Text file is in memory, without a corresponding file on disk

    :type: bool
    """

    is_modified: bool
    """ Text file on disk is different than the one in memory

    :type: bool
    """

    lines: bpy_prop_collection[TextLine]
    """ Lines of text

    :type: bpy_prop_collection[TextLine]
    """

    select_end_character: int
    """ Index of character after end of selection in the selection end line

    :type: int
    """

    select_end_line: TextLine
    """ End line of selection

    :type: TextLine
    """

    select_end_line_index: int
    """ Index of last TextLine in selection

    :type: int
    """

    use_module: bool
    """ Run this text as a Python script on loading

    :type: bool
    """

    def clear(self):
        """clear the text block"""
        ...

    def write(self, text: str | typing.Any):
        """write text at the cursor location and advance to the end of the text block

        :param text: New text for this data-block
        :type text: str | typing.Any
        """
        ...

    def from_string(self, text: str | typing.Any):
        """Replace text with this string.

        :param text:
        :type text: str | typing.Any
        """
        ...

    def as_string(self) -> str | typing.Any:
        """Return the text as a string

        :return:
        :rtype: str | typing.Any
        """
        ...

    def is_syntax_highlight_supported(self) -> bool:
        """Returns True if the editor supports syntax highlighting for the current text datablock

        :return:
        :rtype: bool
        """
        ...

    def select_set(
        self,
        line_start: int | None,
        char_start: int | None,
        line_end: int | None,
        char_end: int | None,
    ):
        """Set selection range by line and character index

        :param line_start: Start Line
        :type line_start: int | None
        :param char_start: Start Character
        :type char_start: int | None
        :param line_end: End Line
        :type line_end: int | None
        :param char_end: End Character
        :type char_end: int | None
        """
        ...

    def cursor_set(
        self,
        line: int | None,
        character: typing.Any | None = 0,
        select: bool | typing.Any | None = False,
    ):
        """Set cursor by line and (optionally) character index

        :param line: Line
        :type line: int | None
        :param character: Character
        :type character: typing.Any | None
        :param select: Select when moving the cursor
        :type select: bool | typing.Any | None
        """
        ...

    def as_module(self): ...
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

    def region_as_string(self, range=None) -> str:
        """

                :param range: The region of text to be returned, defaulting to the selection when no range is passed.
        Each int pair represents a line and column: ((start_line, start_column), (end_line, end_column))
        The values match Python's slicing logic (negative values count backwards from the end, the end value is not inclusive).
                :return: The specified region as a string.
                :rtype: str
        """
        ...

    def region_from_string(self, body: str | None, range=None):
        """

                :param body: The text to be inserted.
                :type body: str | None
                :param range: The region of text to be returned, defaulting to the selection when no range is passed.
        Each int pair represents a line and column: ((start_line, start_column), (end_line, end_column))
        The values match Python's slicing logic (negative values count backwards from the end, the end value is not inclusive).
        """
        ...
