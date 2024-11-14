import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .eq_curve_mapping_data import EQCurveMappingData
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence_modifier import SequenceModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SoundEqualizerModifier(SequenceModifier, bpy_struct):
    """Equalize audio"""

    graphics: bpy_prop_collection[EQCurveMappingData]
    """ Graphical definition equalization

    :type: bpy_prop_collection[EQCurveMappingData]
    """

    def new_graphic(
        self, min_freq: float | None, max_freq: float | None
    ) -> EQCurveMappingData:
        """Add a new EQ band

        :param min_freq: Minimum Frequency, Minimum Frequency
        :type min_freq: float | None
        :param max_freq: Maximum Frequency, Maximum Frequency
        :type max_freq: float | None
        :return: Newly created graphical Equalizer definition
        :rtype: EQCurveMappingData
        """
        ...

    def clear_soundeqs(self):
        """Remove all graphical equalizers from the Equalizer modifier"""
        ...

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
