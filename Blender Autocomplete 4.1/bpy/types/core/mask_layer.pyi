import typing
import collections.abc
import mathutils
from .mask_splines import MaskSplines
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaskLayer(bpy_struct):
    """Single layer used for masking pixels"""

    alpha: float
    """ Render Opacity

    :type: float
    """

    blend: str
    """ Method of blending mask layers

    :type: str
    """

    falloff: str
    """ Falloff type the feather

    :type: str
    """

    hide: bool
    """ Restrict visibility in the viewport

    :type: bool
    """

    hide_render: bool
    """ Restrict renderability

    :type: bool
    """

    hide_select: bool
    """ Restrict selection in the viewport

    :type: bool
    """

    invert: bool
    """ Invert the mask black/white

    :type: bool
    """

    name: str
    """ Unique name of layer

    :type: str
    """

    select: bool
    """ Layer is selected for editing in the Dope Sheet

    :type: bool
    """

    splines: MaskSplines
    """ Collection of splines which defines this layer

    :type: MaskSplines
    """

    use_fill_holes: bool
    """ Calculate holes when filling overlapping curves

    :type: bool
    """

    use_fill_overlap: bool
    """ Calculate self intersections and overlap before filling

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
