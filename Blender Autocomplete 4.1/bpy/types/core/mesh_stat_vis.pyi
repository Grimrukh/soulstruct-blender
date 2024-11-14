import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshStatVis(bpy_struct):
    distort_max: float
    """ Maximum angle to display

    :type: float
    """

    distort_min: float
    """ Minimum angle to display

    :type: float
    """

    overhang_axis: str
    """ 

    :type: str
    """

    overhang_max: float
    """ Maximum angle to display

    :type: float
    """

    overhang_min: float
    """ Minimum angle to display

    :type: float
    """

    sharp_max: float
    """ Maximum angle to display

    :type: float
    """

    sharp_min: float
    """ Minimum angle to display

    :type: float
    """

    thickness_max: float
    """ Maximum for measuring thickness

    :type: float
    """

    thickness_min: float
    """ Minimum for measuring thickness

    :type: float
    """

    thickness_samples: int
    """ Number of samples to test per face

    :type: int
    """

    type: str
    """ Type of data to visualize/check

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
