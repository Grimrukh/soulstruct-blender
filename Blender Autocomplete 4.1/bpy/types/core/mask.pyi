import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .anim_data import AnimData
from .id import ID
from .mask_layers import MaskLayers

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Mask(ID, bpy_struct):
    """Mask data-block defining mask for compositing"""

    active_layer_index: int | None
    """ Index of active layer in list of all mask's layers

    :type: int | None
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    frame_end: int
    """ Final frame of the mask (used for sequencer)

    :type: int
    """

    frame_start: int
    """ First frame of the mask (used for sequencer)

    :type: int
    """

    layers: MaskLayers
    """ Collection of layers which defines this mask

    :type: MaskLayers
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
