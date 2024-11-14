import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .dynamic_paint_brush_settings import DynamicPaintBrushSettings
from .dynamic_paint_canvas_settings import DynamicPaintCanvasSettings
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DynamicPaintModifier(Modifier, bpy_struct):
    """Dynamic Paint modifier"""

    brush_settings: DynamicPaintBrushSettings
    """ 

    :type: DynamicPaintBrushSettings
    """

    canvas_settings: DynamicPaintCanvasSettings
    """ 

    :type: DynamicPaintCanvasSettings
    """

    ui_type: str
    """ 

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
