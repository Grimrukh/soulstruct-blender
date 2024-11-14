import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .dash_gpencil_modifier_segment import DashGpencilModifierSegment
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DashGpencilModifierData(GpencilModifier, bpy_struct):
    """Create dot-dash effect for strokes"""

    dash_offset: int
    """ Offset into each stroke before the beginning of the dashed segment generation

    :type: int
    """

    invert_layer_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_layers: bool
    """ Inverse filter

    :type: bool
    """

    invert_material_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_materials: bool
    """ Inverse filter

    :type: bool
    """

    layer: str
    """ Layer name

    :type: str
    """

    layer_pass: int
    """ Layer pass index

    :type: int
    """

    material: Material
    """ Material used for filtering effect

    :type: Material
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    segment_active_index: int
    """ Active index in the segment list

    :type: int
    """

    segments: bpy_prop_collection[DashGpencilModifierSegment]
    """ 

    :type: bpy_prop_collection[DashGpencilModifierSegment]
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
