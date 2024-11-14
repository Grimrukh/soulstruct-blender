import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Stereo3dFormat(bpy_struct):
    """Settings for stereo output"""

    anaglyph_type: str
    """ 

    :type: str
    """

    display_mode: str
    """ 

    :type: str
    """

    interlace_type: str
    """ 

    :type: str
    """

    use_interlace_swap: bool
    """ Swap left and right stereo channels

    :type: bool
    """

    use_sidebyside_crosseyed: bool
    """ Right eye should see left image and vice versa

    :type: bool
    """

    use_squeezed_frame: bool
    """ Combine both views in a squeezed image

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
