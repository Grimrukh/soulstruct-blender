import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .timeline_marker import TimelineMarker
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TimelineMarkers(bpy_prop_collection[TimelineMarker], bpy_struct):
    """Collection of timeline markers"""

    def new(
        self, name: str | typing.Any, frame: typing.Any | None = 1
    ) -> TimelineMarker:
        """Add a keyframe to the curve

        :param name: New name for the marker (not unique)
        :type name: str | typing.Any
        :param frame: The frame for the new marker
        :type frame: typing.Any | None
        :return: Newly created timeline marker
        :rtype: TimelineMarker
        """
        ...

    def remove(self, marker: TimelineMarker):
        """Remove a timeline marker

        :param marker: Timeline marker to remove
        :type marker: TimelineMarker
        """
        ...

    def clear(self):
        """Remove all timeline markers"""
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
