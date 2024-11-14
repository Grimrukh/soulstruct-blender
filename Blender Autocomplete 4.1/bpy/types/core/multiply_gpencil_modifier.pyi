import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MultiplyGpencilModifier(GpencilModifier, bpy_struct):
    """Generate multiple strokes from one stroke"""

    distance: float
    """ Distance of duplications

    :type: float
    """

    duplicates: int
    """ How many copies of strokes be displayed

    :type: int
    """

    fading_center: float
    """ Fade center

    :type: float
    """

    fading_opacity: float
    """ Fade influence of stroke's opacity

    :type: float
    """

    fading_thickness: float
    """ Fade influence of stroke's thickness

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

    offset: float
    """ Offset of duplicates. -1 to 1: inner to outer

    :type: float
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    use_fade: bool
    """ Fade the stroke thickness for each generated stroke

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
