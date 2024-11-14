import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SimplifyGpencilModifier(GpencilModifier, bpy_struct):
    """Simplify Stroke modifier"""

    distance: float
    """ Distance between points

    :type: float
    """

    factor: float
    """ Factor of Simplify

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

    length: float
    """ Length of each segment

    :type: float
    """

    material: Material
    """ Material used for filtering effect

    :type: Material
    """

    mode: str
    """ How to simplify the stroke

    :type: str
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    sharp_threshold: float
    """ Preserve corners that have sharper angle than this threshold

    :type: float
    """

    step: int
    """ Number of times to apply simplify

    :type: int
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
