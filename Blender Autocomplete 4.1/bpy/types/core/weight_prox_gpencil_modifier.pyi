import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .object import Object
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WeightProxGpencilModifier(GpencilModifier, bpy_struct):
    """Calculate Vertex Weight dynamically"""

    distance_end: float
    """ Distance mapping to 1.0 weight

    :type: float
    """

    distance_start: float
    """ Distance mapping to 0.0 weight

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

    minimum_weight: float
    """ Minimum value for vertex weight

    :type: float
    """

    object: Object
    """ Object used as distance reference

    :type: Object
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    target_vertex_group: str
    """ Output Vertex group

    :type: str
    """

    use_invert_output: bool
    """ Invert output weight values

    :type: bool
    """

    use_multiply: bool
    """ Multiply the calculated weights with the existing values in the vertex group

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
