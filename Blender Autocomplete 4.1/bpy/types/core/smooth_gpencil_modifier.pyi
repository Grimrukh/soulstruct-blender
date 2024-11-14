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


class SmoothGpencilModifier(GpencilModifier, bpy_struct):
    """Smooth effect modifier"""

    curve: CurveMapping
    """ Custom curve to apply effect

    :type: CurveMapping
    """

    factor: float
    """ Amount of smooth to apply

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

    pass_index: int
    """ Pass index

    :type: int
    """

    step: int
    """ Number of times to apply smooth (high numbers can reduce fps)

    :type: int
    """

    use_custom_curve: bool
    """ Use a custom curve to define smooth effect along the strokes

    :type: bool
    """

    use_edit_position: bool
    """ The modifier affects the position of the point

    :type: bool
    """

    use_edit_strength: bool
    """ The modifier affects the color strength of the point

    :type: bool
    """

    use_edit_thickness: bool
    """ The modifier affects the thickness of the point

    :type: bool
    """

    use_edit_uv: bool
    """ The modifier affects the UV rotation factor of the point

    :type: bool
    """

    use_keep_shape: bool
    """ Smooth the details, but keep the overall shape

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
