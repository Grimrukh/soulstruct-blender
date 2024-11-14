import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence_modifier import SequenceModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequencerTonemapModifierData(SequenceModifier, bpy_struct):
    """Tone mapping modifier"""

    adaptation: float
    """ If 0, global; if 1, based on pixel intensity

    :type: float
    """

    contrast: float
    """ Set to 0 to use estimate from input image

    :type: float
    """

    correction: float
    """ If 0, same for all channels; if 1, each independent

    :type: float
    """

    gamma: float
    """ If not used, set to 1

    :type: float
    """

    intensity: float
    """ If less than zero, darkens image; otherwise, makes it brighter

    :type: float
    """

    key: float
    """ The value the average luminance is mapped to

    :type: float
    """

    offset: float
    """ Normally always 1, but can be used as an extra control to alter the brightness curve

    :type: float
    """

    tonemap_type: str
    """ Tone mapping algorithm

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
