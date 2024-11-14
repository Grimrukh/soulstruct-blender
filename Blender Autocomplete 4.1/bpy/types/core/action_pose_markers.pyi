import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .timeline_marker import TimelineMarker
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ActionPoseMarkers(bpy_prop_collection[TimelineMarker], bpy_struct):
    """Collection of timeline markers"""

    active: TimelineMarker | None
    """ Active pose marker for this action

    :type: TimelineMarker | None
    """

    active_index: int | None
    """ Index of active pose marker

    :type: int | None
    """

    def new(self, name: str | typing.Any) -> TimelineMarker:
        """Add a pose marker to the action

        :param name: New name for the marker (not unique)
        :type name: str | typing.Any
        :return: Newly created marker
        :rtype: TimelineMarker
        """
        ...

    def remove(self, marker: TimelineMarker):
        """Remove a timeline marker

        :param marker: Timeline marker to remove
        :type marker: TimelineMarker
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
