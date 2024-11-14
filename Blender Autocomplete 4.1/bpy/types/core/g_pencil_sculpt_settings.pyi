import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .g_pencil_sculpt_guide import GPencilSculptGuide
from .curve_mapping import CurveMapping

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilSculptSettings(bpy_struct):
    """General properties for Grease Pencil stroke sculpting tools"""

    guide: GPencilSculptGuide
    """ 

    :type: GPencilSculptGuide
    """

    intersection_threshold: float
    """ Threshold for stroke intersections

    :type: float
    """

    lock_axis: str
    """ 

    :type: str
    """

    multiframe_falloff_curve: CurveMapping
    """ Custom curve to control falloff of brush effect by Grease Pencil frames

    :type: CurveMapping
    """

    thickness_primitive_curve: CurveMapping
    """ Custom curve to control primitive thickness

    :type: CurveMapping
    """

    use_automasking_layer_active: bool
    """ Affect only the Active Layer

    :type: bool
    """

    use_automasking_layer_stroke: bool
    """ Affect only strokes below the cursor

    :type: bool
    """

    use_automasking_material_active: bool
    """ Affect only the Active Material

    :type: bool
    """

    use_automasking_material_stroke: bool
    """ Affect only strokes below the cursor

    :type: bool
    """

    use_automasking_stroke: bool
    """ Affect only strokes below the cursor

    :type: bool
    """

    use_multiframe_falloff: bool
    """ Use falloff effect when edit in multiframe mode to compute brush effect by frame

    :type: bool
    """

    use_scale_thickness: bool
    """ Scale the stroke thickness when transforming strokes

    :type: bool
    """

    use_thickness_curve: bool
    """ Use curve to define primitive stroke thickness

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
