import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .curve_mapping import CurveMapping
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GreasePencilNoiseModifier(Modifier, bpy_struct):
    """Noise effect modifier"""

    custom_curve: CurveMapping
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

    noise_offset: float
    """ Offset the noise along the strokes

    :type: float
    """

    noise_scale: float
    """ Scale the noise frequency

    :type: float
    """

    open_influence_panel: bool
    """ 

    :type: bool
    """

    open_random_panel: bool
    """ 

    :type: bool
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

    use_random: bool
    """ Use random values over time

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
