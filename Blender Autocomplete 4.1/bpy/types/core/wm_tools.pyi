import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .work_space_tool import WorkSpaceTool

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class wmTools(bpy_prop_collection[WorkSpaceTool], bpy_struct):
    def from_space_view3d_mode(
        self, mode: str | None, create: bool | typing.Any | None = False
    ) -> WorkSpaceTool:
        """

        :param mode:
        :type mode: str | None
        :param create: Create
        :type create: bool | typing.Any | None
        :return:
        :rtype: WorkSpaceTool
        """
        ...

    def from_space_image_mode(
        self, mode: str | None, create: bool | typing.Any | None = False
    ) -> WorkSpaceTool:
        """

        :param mode:
        :type mode: str | None
        :param create: Create
        :type create: bool | typing.Any | None
        :return:
        :rtype: WorkSpaceTool
        """
        ...

    def from_space_node(
        self, create: bool | typing.Any | None = False
    ) -> WorkSpaceTool:
        """

        :param create: Create
        :type create: bool | typing.Any | None
        :return:
        :rtype: WorkSpaceTool
        """
        ...

    def from_space_sequencer(
        self, mode: str | None, create: bool | typing.Any | None = False
    ) -> WorkSpaceTool:
        """

        :param mode:
        :type mode: str | None
        :param create: Create
        :type create: bool | typing.Any | None
        :return:
        :rtype: WorkSpaceTool
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
