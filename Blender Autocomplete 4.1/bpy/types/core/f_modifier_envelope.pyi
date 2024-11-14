import typing
import collections.abc
import mathutils
from .f_modifier import FModifier
from .f_modifier_envelope_control_points import FModifierEnvelopeControlPoints
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FModifierEnvelope(FModifier, bpy_struct):
    """Scale the values of the modified F-Curve"""

    control_points: FModifierEnvelopeControlPoints
    """ Control points defining the shape of the envelope

    :type: FModifierEnvelopeControlPoints
    """

    default_max: float
    """ Upper distance from Reference Value for 1:1 default influence

    :type: float
    """

    default_min: float
    """ Lower distance from Reference Value for 1:1 default influence

    :type: float
    """

    reference_value: float
    """ Value that envelope's influence is centered around / based on

    :type: float
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
