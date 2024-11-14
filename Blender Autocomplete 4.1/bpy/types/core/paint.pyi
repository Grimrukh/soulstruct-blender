import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .paint_tool_slot import PaintToolSlot
from .palette import Palette
from .bpy_struct import bpy_struct
from .brush import Brush
from .curve_mapping import CurveMapping

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Paint(bpy_struct):
    brush: Brush
    """ Active Brush

    :type: Brush
    """

    cavity_curve: CurveMapping
    """ Editable cavity curve

    :type: CurveMapping
    """

    palette: Palette
    """ Active Palette

    :type: Palette
    """

    show_brush: bool
    """ 

    :type: bool
    """

    show_brush_on_surface: bool
    """ 

    :type: bool
    """

    show_low_resolution: bool
    """ For multires, show low resolution while navigating the view

    :type: bool
    """

    tile_offset: mathutils.Vector
    """ Stride at which tiled strokes are copied

    :type: mathutils.Vector
    """

    tile_x: bool
    """ Tile along X axis

    :type: bool
    """

    tile_y: bool
    """ Tile along Y axis

    :type: bool
    """

    tile_z: bool
    """ Tile along Z axis

    :type: bool
    """

    tool_slots: bpy_prop_collection[PaintToolSlot]
    """ 

    :type: bpy_prop_collection[PaintToolSlot]
    """

    use_cavity: bool
    """ Mask painting according to mesh geometry cavity

    :type: bool
    """

    use_sculpt_delay_updates: bool
    """ Update the geometry when it enters the view, providing faster view navigation

    :type: bool
    """

    use_symmetry_feather: bool
    """ Reduce the strength of the brush where it overlaps symmetrical daubs

    :type: bool
    """

    use_symmetry_x: bool
    """ Mirror brush across the X axis

    :type: bool
    """

    use_symmetry_y: bool
    """ Mirror brush across the Y axis

    :type: bool
    """

    use_symmetry_z: bool
    """ Mirror brush across the Z axis

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
