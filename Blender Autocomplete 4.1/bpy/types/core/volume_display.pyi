import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VolumeDisplay(bpy_struct):
    """Volume object display settings for 3D viewport"""

    density: float
    """ Thickness of volume display in the viewport

    :type: float
    """

    interpolation_method: str
    """ Interpolation method to use for volumes in solid mode

    :type: str
    """

    slice_axis: str
    """ 

    :type: str
    """

    slice_depth: float
    """ Position of the slice

    :type: float
    """

    use_slice: bool
    """ Perform a single slice of the domain object

    :type: bool
    """

    wireframe_detail: str
    """ Amount of detail for wireframe display

    :type: str
    """

    wireframe_type: str
    """ Type of wireframe display

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
