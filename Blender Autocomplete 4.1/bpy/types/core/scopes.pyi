import typing
import collections.abc
import mathutils
from .histogram import Histogram
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Scopes(bpy_struct):
    """Scopes for statistical view of an image"""

    accuracy: float
    """ Proportion of original image source pixel lines to sample

    :type: float
    """

    histogram: Histogram
    """ Histogram for viewing image statistics

    :type: Histogram
    """

    use_full_resolution: bool
    """ Sample every pixel of the image

    :type: bool
    """

    vectorscope_alpha: float
    """ Opacity of the points

    :type: float
    """

    vectorscope_mode: str
    """ 

    :type: str
    """

    waveform_alpha: float
    """ Opacity of the points

    :type: float
    """

    waveform_mode: str
    """ 

    :type: str
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
