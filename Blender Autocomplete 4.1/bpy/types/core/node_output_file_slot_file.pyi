import typing
import collections.abc
import mathutils
from .image_format_settings import ImageFormatSettings
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeOutputFileSlotFile(bpy_struct):
    """Single layer file slot of the file output node"""

    format: ImageFormatSettings
    """ 

    :type: ImageFormatSettings
    """

    path: str
    """ Subpath used for this slot

    :type: str
    """

    save_as_render: bool
    """ Apply render part of display transform when saving byte image

    :type: bool
    """

    use_node_format: bool
    """ 

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
