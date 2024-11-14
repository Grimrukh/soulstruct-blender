import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .curve_mapping import CurveMapping
from .object import Object
from .color_ramp import ColorRamp
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TintGpencilModifier(GpencilModifier, bpy_struct):
    """Tint modifier"""

    color: mathutils.Color
    """ Color used for tinting

    :type: mathutils.Color
    """

    colors: ColorRamp
    """ Color ramp used to define tinting colors

    :type: ColorRamp
    """

    curve: CurveMapping
    """ Custom curve to apply effect

    :type: CurveMapping
    """

    factor: float
    """ Factor for tinting

    :type: float
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

    invert_vertex: bool
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

    object: Object
    """ Parent object to define the center of the effect

    :type: Object
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    radius: float
    """ Defines the maximum distance of the effect

    :type: float
    """

    tint_type: str
    """ Select type of tinting algorithm

    :type: str
    """

    use_custom_curve: bool
    """ Use a custom curve to define vertex color effect along the strokes

    :type: bool
    """

    use_weight_factor: bool
    """ Use weight to modulate effect

    :type: bool
    """

    vertex_group: str
    """ Vertex group name for modulating the deform

    :type: str
    """

    vertex_mode: str
    """ Defines how vertex color affect to the strokes

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
