import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequencerPreviewOverlay(bpy_struct):
    show_annotation: bool
    """ Show annotations for this view

    :type: bool
    """

    show_cursor: bool
    """ 

    :type: bool
    """

    show_image_outline: bool
    """ 

    :type: bool
    """

    show_metadata: bool
    """ Show metadata of first visible strip

    :type: bool
    """

    show_safe_areas: bool
    """ Show TV title safe and action safe areas in preview

    :type: bool
    """

    show_safe_center: bool
    """ Show safe areas to fit content in a different aspect ratio

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
