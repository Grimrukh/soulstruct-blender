import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .curve_mapping import CurveMapping
from .object import Object
from .color_ramp import ColorRamp
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GreasePencilTintModifier(Modifier, bpy_struct):
    color: mathutils.Color
    """ Color used for tinting

    :type: mathutils.Color
    """

    color_mode: str
    """ Attributes to modify

    :type: str
    """

    color_ramp: ColorRamp
    """ Gradient tinting colors

    :type: ColorRamp
    """

    custom_curve: CurveMapping
    """ Custom curve to apply effect

    :type: CurveMapping
    """

    factor: float
    """ Factor for tinting

    :type: float
    """

    invert_layer_filter: bool
    """ Invert layer filter

    :type: bool
    """

    invert_layer_pass_filter: bool
    """ Invert layer pass filter

    :type: bool
    """

    invert_material_filter: bool
    """ Invert material filter

    :type: bool
    """

    invert_material_pass_filter: bool
    """ Invert material pass filter

    :type: bool
    """

    invert_vertex_group: bool
    """ Invert vertex group weights

    :type: bool
    """

    layer_filter: str
    """ Layer name

    :type: str
    """

    layer_pass_filter: int
    """ Layer pass filter

    :type: int
    """

    material_filter: Material
    """ Material used for filtering

    :type: Material
    """

    material_pass_filter: int
    """ Material pass

    :type: int
    """

    object: Object
    """ Object used for the gradient direction

    :type: Object
    """

    open_influence_panel: bool
    """ 

    :type: bool
    """

    radius: float
    """ Influence distance from the object

    :type: float
    """

    tint_mode: str
    """ 

    :type: str
    """

    use_custom_curve: bool
    """ Use a custom curve to define a factor along the strokes

    :type: bool
    """

    use_layer_pass_filter: bool
    """ Use layer pass filter

    :type: bool
    """

    use_material_pass_filter: bool
    """ Use material pass filter

    :type: bool
    """

    use_weight_as_factor: bool
    """ Use vertex group weight as factor instead of influence

    :type: bool
    """

    vertex_group_name: str
    """ Vertex group name for modulating the deform

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
