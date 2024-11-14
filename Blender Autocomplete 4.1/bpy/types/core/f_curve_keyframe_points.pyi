import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .keyframe import Keyframe

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FCurveKeyframePoints(bpy_prop_collection[Keyframe], bpy_struct):
    """Collection of keyframe points"""

    def insert(
        self,
        frame: float | None,
        value: float | None,
        options: set[str] | None = {},
        keyframe_type: str | None = "KEYFRAME",
    ) -> Keyframe:
        """Add a keyframe point to a F-Curve

                :param frame: X Value of this keyframe point
                :type frame: float | None
                :param value: Y Value of this keyframe point
                :type value: float | None
                :param options: Keyframe options

        REPLACE
        Replace -- Don't add any new keyframes, but just replace existing ones.

        NEEDED
        Needed -- Only adds keyframes that are needed.

        FAST
        Fast -- Fast keyframe insertion to avoid recalculating the curve each time.
                :type options: set[str] | None
                :param keyframe_type: Type of keyframe to insert
                :type keyframe_type: str | None
                :return: Newly created keyframe
                :rtype: Keyframe
        """
        ...

    def add(self, count: int | None):
        """Add a keyframe point to a F-Curve

        :param count: Number, Number of points to add to the spline
        :type count: int | None
        """
        ...

    def remove(self, keyframe: Keyframe, fast: bool | typing.Any | None = False):
        """Remove keyframe from an F-Curve

        :param keyframe: Keyframe to remove
        :type keyframe: Keyframe
        :param fast: Fast, Fast keyframe removal to avoid recalculating the curve each time
        :type fast: bool | typing.Any | None
        """
        ...

    def clear(self):
        """Remove all keyframes from an F-Curve"""
        ...

    def sort(self):
        """Ensure all keyframe points are chronologically sorted"""
        ...

    def deduplicate(self):
        """Ensure there are no duplicate keys. Assumes that the points have already been sorted"""
        ...

    def handles_recalc(self):
        """Update handles after modifications to the keyframe points, to update things like auto-clamping"""
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
