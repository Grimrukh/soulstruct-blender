import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .f_modifier_envelope_control_point import FModifierEnvelopeControlPoint
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FModifierEnvelopeControlPoints(
    bpy_prop_collection[FModifierEnvelopeControlPoint], bpy_struct
):
    """Control points defining the shape of the envelope"""

    def add(self, frame: float | None) -> FModifierEnvelopeControlPoint:
        """Add a control point to a FModifierEnvelope

        :param frame: Frame to add this control-point
        :type frame: float | None
        :return: Newly created control-point
        :rtype: FModifierEnvelopeControlPoint
        """
        ...

    def remove(self, point: FModifierEnvelopeControlPoint):
        """Remove a control-point from an FModifierEnvelope

        :param point: Control-point to remove
        :type point: FModifierEnvelopeControlPoint
        """
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
