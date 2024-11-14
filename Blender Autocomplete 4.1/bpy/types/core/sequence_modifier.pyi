import typing
import collections.abc
import mathutils
from .mask import Mask
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequenceModifier(bpy_struct):
    """Modifier for sequence strip"""

    input_mask_id: Mask
    """ Mask ID used as mask input for the modifier

    :type: Mask
    """

    input_mask_strip: Sequence
    """ Strip used as mask input for the modifier

    :type: Sequence
    """

    input_mask_type: str
    """ Type of input data used for mask

    :type: str
    """

    mask_time: str
    """ Time to use for the Mask animation

    :type: str
    """

    mute: bool
    """ Mute this modifier

    :type: bool
    """

    name: str
    """ 

    :type: str
    """

    show_expanded: bool
    """ Mute expanded settings for the modifier

    :type: bool
    """

    type: str
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
