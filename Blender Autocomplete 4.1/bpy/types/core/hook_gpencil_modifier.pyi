import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .material import Material
from .curve_mapping import CurveMapping
from .object import Object
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class HookGpencilModifier(GpencilModifier, bpy_struct):
    """Hook modifier to modify the location of stroke points"""

    center: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    falloff_curve: CurveMapping
    """ Custom falloff curve

    :type: CurveMapping
    """

    falloff_radius: float
    """ If not zero, the distance from the hook where influence ends

    :type: float
    """

    falloff_type: str
    """ 

    :type: str
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

    matrix_inverse: mathutils.Matrix
    """ Reverse the transformation between this object and its target

    :type: mathutils.Matrix
    """

    object: Object
    """ Parent Object for hook, also recalculates and clears offset

    :type: Object
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    strength: float
    """ Relative force of the hook

    :type: float
    """

    subtarget: str
    """ Name of Parent Bone for hook (if applicable), also recalculates and clears offset

    :type: str
    """

    use_falloff_uniform: bool
    """ Compensate for non-uniform object scale

    :type: bool
    """

    vertex_group: str
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
