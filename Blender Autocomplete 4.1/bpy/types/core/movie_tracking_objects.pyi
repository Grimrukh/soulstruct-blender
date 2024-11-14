import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_tracking_object import MovieTrackingObject

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingObjects(bpy_prop_collection[MovieTrackingObject], bpy_struct):
    """Collection of movie tracking objects"""

    active: MovieTrackingObject | None
    """ Active object in this tracking data object

    :type: MovieTrackingObject | None
    """

    def new(self, name: str | typing.Any) -> MovieTrackingObject:
        """Add tracking object to this movie clip

        :param name: Name of new object
        :type name: str | typing.Any
        :return: New motion tracking object
        :rtype: MovieTrackingObject
        """
        ...

    def remove(self, object: MovieTrackingObject):
        """Remove tracking object from this movie clip

        :param object: Motion tracking object to be removed
        :type object: MovieTrackingObject
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
