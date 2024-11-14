import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LengthGpencilModifier(GpencilModifier, bpy_struct):
    """Stretch or shrink strokes"""

    end_factor: float
    """ Added length to the end of each stroke relative to its length

    :type: float
    """

    end_length: float
    """ Absolute added length to the end of each stroke

    :type: float
    """

    invert_curvature: bool
    """ Invert the curvature of the stroke's extension

    :type: bool
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

    max_angle: float
    """ Ignore points on the stroke that deviate from their neighbors by more than this angle when determining the extrapolation shape

    :type: float
    """

    mode: str
    """ Mode to define length

    :type: str
    """

    overshoot_factor: float
    """ Defines what portion of the stroke is used for the calculation of the extension

    :type: float
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    point_density: float
    """ Multiplied by Start/End for the total added point count

    :type: float
    """

    random_end_factor: float
    """ Size of random length added to the end of each stroke

    :type: float
    """

    random_offset: float
    """ Smoothly offset each stroke's random value

    :type: float
    """

    random_start_factor: float
    """ Size of random length added to the start of each stroke

    :type: float
    """

    seed: int
    """ Random seed

    :type: int
    """

    segment_influence: float
    """ Factor to determine how much the length of the individual segments should influence the final computed curvature. Higher factors makes small segments influence the overall curvature less

    :type: float
    """

    start_factor: float
    """ Added length to the start of each stroke relative to its length

    :type: float
    """

    start_length: float
    """ Absolute added length to the start of each stroke

    :type: float
    """

    step: int
    """ Number of frames between randomization steps

    :type: int
    """

    use_curvature: bool
    """ Follow the curvature of the stroke

    :type: bool
    """

    use_random: bool
    """ Use random values over time

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
