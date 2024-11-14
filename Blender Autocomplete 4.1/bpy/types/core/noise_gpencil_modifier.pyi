import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .curve_mapping import CurveMapping
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NoiseGpencilModifier(GpencilModifier, bpy_struct):
    """Noise effect modifier"""

    curve: CurveMapping
    """ Custom curve to apply effect

    :type: CurveMapping
    """

    factor: float
    """ Amount of noise to apply

    :type: float
    """

    factor_strength: float
    """ Amount of noise to apply to opacity

    :type: float
    """

    factor_thickness: float
    """ Amount of noise to apply to thickness

    :type: float
    """

    factor_uvs: float
    """ Amount of noise to apply to UV rotation

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

    noise_offset: float
    """ Offset the noise along the strokes

    :type: float
    """

    noise_scale: float
    """ Scale the noise frequency

    :type: float
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    random_mode: str
    """ Where to perform randomization

    :type: str
    """

    seed: int
    """ Random seed

    :type: int
    """

    step: int
    """ Number of frames between randomization steps

    :type: int
    """

    use_custom_curve: bool
    """ Use a custom curve to define noise effect along the strokes

    :type: bool
    """

    use_random: bool
    """ Use random values over time

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
