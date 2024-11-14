import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .effect_sequence import EffectSequence

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TransformSequence(EffectSequence, Sequence, bpy_struct):
    """Sequence strip applying affine transformations to other strips"""

    input_1: Sequence
    """ First input for the effect strip

    :type: Sequence
    """

    input_count: int
    """ 

    :type: int
    """

    interpolation: str
    """ Method to determine how missing pixels are created

    :type: str
    """

    rotation_start: float
    """ Degrees to rotate the input

    :type: float
    """

    scale_start_x: float
    """ Amount to scale the input in the X axis

    :type: float
    """

    scale_start_y: float
    """ Amount to scale the input in the Y axis

    :type: float
    """

    translate_start_x: float
    """ Amount to move the input on the X axis

    :type: float
    """

    translate_start_y: float
    """ Amount to move the input on the Y axis

    :type: float
    """

    translation_unit: str
    """ Unit of measure to translate the input

    :type: str
    """

    use_uniform_scale: bool
    """ Scale uniformly, preserving aspect ratio

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
