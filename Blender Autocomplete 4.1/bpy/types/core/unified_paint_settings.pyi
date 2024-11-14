import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UnifiedPaintSettings(bpy_struct):
    """Overrides for some of the active brush's settings"""

    color: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    input_samples: int
    """ Number of input samples to average together to smooth the brush stroke

    :type: int
    """

    secondary_color: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    size: int
    """ Radius of the brush

    :type: int
    """

    strength: float
    """ How powerful the effect of the brush is when applied

    :type: float
    """

    unprojected_radius: float
    """ Radius of brush in Blender units

    :type: float
    """

    use_locked_size: str
    """ Measure brush size relative to the view or the scene

    :type: str
    """

    use_unified_color: bool
    """ Instead of per-brush color, the color is shared across brushes

    :type: bool
    """

    use_unified_input_samples: bool
    """ Instead of per-brush input samples, the value is shared across brushes

    :type: bool
    """

    use_unified_size: bool
    """ Instead of per-brush radius, the radius is shared across brushes

    :type: bool
    """

    use_unified_strength: bool
    """ Instead of per-brush strength, the strength is shared across brushes

    :type: bool
    """

    use_unified_weight: bool
    """ Instead of per-brush weight, the weight is shared across brushes

    :type: bool
    """

    weight: float
    """ Weight to assign in vertex groups

    :type: float
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
