import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .render_view import RenderView
from .render_layer import RenderLayer

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RenderResult(bpy_struct):
    """Result of rendering, including all layers and passes"""

    layers: bpy_prop_collection[RenderLayer]
    """ 

    :type: bpy_prop_collection[RenderLayer]
    """

    resolution_x: int
    """ 

    :type: int
    """

    resolution_y: int
    """ 

    :type: int
    """

    views: bpy_prop_collection[RenderView]
    """ 

    :type: bpy_prop_collection[RenderView]
    """

    def load_from_file(self, filepath: str | typing.Any):
        """Copies the pixels of this render result from an image file

        :param filepath: File Name, Filename to load into this render tile, must be no smaller than the render result
        :type filepath: str | typing.Any
        """
        ...

    def stamp_data_add_field(self, field: str | typing.Any, value: str | typing.Any):
        """Add engine-specific stamp data to the result

        :param field: Field, Name of the stamp field to add
        :type field: str | typing.Any
        :param value: Value, Value of the stamp data
        :type value: str | typing.Any
        """
        ...

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
