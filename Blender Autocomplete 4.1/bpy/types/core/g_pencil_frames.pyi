import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .g_pencil_frame import GPencilFrame
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilFrames(bpy_prop_collection[GPencilFrame], bpy_struct):
    """Collection of grease pencil frames"""

    def new(
        self, frame_number: int | None, active: bool | typing.Any | None = False
    ) -> GPencilFrame:
        """Add a new grease pencil frame

        :param frame_number: Frame Number, The frame on which this sketch appears
        :type frame_number: int | None
        :param active: Active
        :type active: bool | typing.Any | None
        :return: The newly created frame
        :rtype: GPencilFrame
        """
        ...

    def remove(self, frame: GPencilFrame):
        """Remove a grease pencil frame

        :param frame: Frame, The frame to remove
        :type frame: GPencilFrame
        """
        ...

    def copy(self, source: GPencilFrame) -> GPencilFrame:
        """Copy a grease pencil frame

        :param source: Source, The source frame
        :type source: GPencilFrame
        :return: The newly copied frame
        :rtype: GPencilFrame
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
