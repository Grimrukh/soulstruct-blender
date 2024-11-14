import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .vector_font import VectorFont
from .text_character_format import TextCharacterFormat
from .bpy_struct import bpy_struct
from .text_box import TextBox
from .id import ID
from .object import Object
from .curve import Curve

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TextCurve(Curve, ID, bpy_struct):
    """Curve data-block used for storing text"""

    active_textbox: int | None
    """ 

    :type: int | None
    """

    align_x: str
    """ Text horizontal alignment from the object center

    :type: str
    """

    align_y: str
    """ Text vertical alignment from the object center

    :type: str
    """

    body: str
    """ Content of this text object

    :type: str
    """

    body_format: bpy_prop_collection[TextCharacterFormat]
    """ Stores the style of each character

    :type: bpy_prop_collection[TextCharacterFormat]
    """

    edit_format: TextCharacterFormat
    """ Editing settings character formatting

    :type: TextCharacterFormat
    """

    family: str
    """ Use objects as font characters (give font objects a common name followed by the character they represent, eg. 'family-a', 'family-b', etc, set this setting to 'family-', and turn on Vertex Instancing)

    :type: str
    """

    follow_curve: Object
    """ Curve deforming text object

    :type: Object
    """

    font: VectorFont
    """ 

    :type: VectorFont
    """

    font_bold: VectorFont
    """ 

    :type: VectorFont
    """

    font_bold_italic: VectorFont
    """ 

    :type: VectorFont
    """

    font_italic: VectorFont
    """ 

    :type: VectorFont
    """

    has_selection: bool
    """ Whether there is any text selected

    :type: bool
    """

    is_select_bold: bool
    """ Whether the selected text is bold

    :type: bool
    """

    is_select_italic: bool
    """ Whether the selected text is italics

    :type: bool
    """

    is_select_smallcaps: bool
    """ Whether the selected text is small caps

    :type: bool
    """

    is_select_underline: bool
    """ Whether the selected text is underlined

    :type: bool
    """

    offset_x: float
    """ Horizontal offset from the object origin

    :type: float
    """

    offset_y: float
    """ Vertical offset from the object origin

    :type: float
    """

    overflow: str
    """ Handle the text behavior when it doesn't fit in the text boxes

    :type: str
    """

    shear: float
    """ Italic angle of the characters

    :type: float
    """

    size: float
    """ 

    :type: float
    """

    small_caps_scale: float
    """ Scale of small capitals

    :type: float
    """

    space_character: float
    """ 

    :type: float
    """

    space_line: float
    """ 

    :type: float
    """

    space_word: float
    """ 

    :type: float
    """

    text_boxes: bpy_prop_collection[TextBox]
    """ 

    :type: bpy_prop_collection[TextBox]
    """

    underline_height: float
    """ 

    :type: float
    """

    underline_position: float
    """ Vertical position of underline

    :type: float
    """

    use_fast_edit: bool
    """ Don't fill polygons while editing

    :type: bool
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
