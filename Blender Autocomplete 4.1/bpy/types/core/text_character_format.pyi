import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TextCharacterFormat(bpy_struct):
    """Text character formatting settings"""

    kerning: float
    """ Spacing between characters

    :type: float
    """

    material_index: int
    """ Material slot index of this character

    :type: int
    """

    use_bold: bool
    """ 

    :type: bool
    """

    use_italic: bool
    """ 

    :type: bool
    """

    use_small_caps: bool
    """ 

    :type: bool
    """

    use_underline: bool
    """ 

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
