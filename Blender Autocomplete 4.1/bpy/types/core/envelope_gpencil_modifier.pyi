import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class EnvelopeGpencilModifier(GpencilModifier, bpy_struct):
    """Envelope stroke effect modifier"""

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

    mat_nr: int
    """ The material to use for the new strokes

    :type: int
    """

    material: Material
    """ Material used for filtering effect

    :type: Material
    """

    mode: str
    """ Algorithm to use for generating the envelope

    :type: str
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    skip: int
    """ The number of generated segments to skip to reduce complexity

    :type: int
    """

    spread: int
    """ The number of points to skip to create straight segments

    :type: int
    """

    strength: float
    """ Multiplier for the strength of the new strokes

    :type: float
    """

    thickness: float
    """ Multiplier for the thickness of the new strokes

    :type: float
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
