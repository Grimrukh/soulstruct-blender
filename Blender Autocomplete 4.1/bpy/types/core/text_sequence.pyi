import typing
import collections.abc
import mathutils
from .struct import Struct
from .vector_font import VectorFont
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .bpy_prop_array import bpy_prop_array
from .effect_sequence import EffectSequence

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TextSequence(EffectSequence, Sequence, bpy_struct):
    """Sequence strip creating text"""

    align_x: str
    """ Align the text along the X axis, relative to the text bounds

    :type: str
    """

    align_y: str
    """ Align the text along the Y axis, relative to the text bounds

    :type: str
    """

    box_color: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    box_margin: float
    """ Box margin as factor of image width

    :type: float
    """

    color: bpy_prop_array[float]
    """ Text color

    :type: bpy_prop_array[float]
    """

    font: VectorFont
    """ Font of the text. Falls back to the UI font by default

    :type: VectorFont
    """

    font_size: float
    """ Size of the text

    :type: float
    """

    input_count: int
    """ 

    :type: int
    """

    location: mathutils.Vector
    """ Location of the text

    :type: mathutils.Vector
    """

    shadow_color: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    text: str
    """ Text that will be displayed

    :type: str
    """

    use_bold: bool
    """ Display text as bold

    :type: bool
    """

    use_box: bool
    """ Display colored box behind text

    :type: bool
    """

    use_italic: bool
    """ Display text as italic

    :type: bool
    """

    use_shadow: bool
    """ Display shadow behind text

    :type: bool
    """

    wrap_width: float
    """ Word wrap width as factor, zero disables

    :type: float
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
