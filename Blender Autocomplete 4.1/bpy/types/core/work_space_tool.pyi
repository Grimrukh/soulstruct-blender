import typing
import collections.abc
import mathutils
from .gizmo_group_properties import GizmoGroupProperties
from .struct import Struct
from .bpy_struct import bpy_struct
from .operator_properties import OperatorProperties

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WorkSpaceTool(bpy_struct):
    has_datablock: bool
    """ 

    :type: bool
    """

    idname: str
    """ 

    :type: str
    """

    idname_fallback: str
    """ 

    :type: str
    """

    index: int
    """ 

    :type: int
    """

    mode: str
    """ 

    :type: str
    """

    space_type: str
    """ 

    :type: str
    """

    use_paint_canvas: bool
    """ Does this tool use a painting canvas

    :type: bool
    """

    widget: str
    """ 

    :type: str
    """

    def setup(
        self,
        idname: str | typing.Any,
        cursor: str | None = "DEFAULT",
        keymap: str | typing.Any = "",
        gizmo_group: str | typing.Any = "",
        data_block: str | typing.Any = "",
        operator: str | typing.Any = "",
        index: typing.Any | None = 0,
        options: set[str] | None = {},
        idname_fallback: str | typing.Any = "",
        keymap_fallback: str | typing.Any = "",
    ):
        """Set the tool settings

        :param idname: Identifier
        :type idname: str | typing.Any
        :param cursor: cursor
        :type cursor: str | None
        :param keymap: Key Map
        :type keymap: str | typing.Any
        :param gizmo_group: Gizmo Group
        :type gizmo_group: str | typing.Any
        :param data_block: Data Block
        :type data_block: str | typing.Any
        :param operator: Operator
        :type operator: str | typing.Any
        :param index: Index
        :type index: typing.Any | None
        :param options: Tool Options
        :type options: set[str] | None
        :param idname_fallback: Fallback Identifier
        :type idname_fallback: str | typing.Any
        :param keymap_fallback: Fallback Key Map
        :type keymap_fallback: str | typing.Any
        """
        ...

    def operator_properties(self, operator: str | typing.Any) -> OperatorProperties:
        """operator_properties

        :param operator:
        :type operator: str | typing.Any
        :return:
        :rtype: OperatorProperties
        """
        ...

    def gizmo_group_properties(self, group: str | typing.Any) -> GizmoGroupProperties:
        """gizmo_group_properties

        :param group:
        :type group: str | typing.Any
        :return:
        :rtype: GizmoGroupProperties
        """
        ...

    def refresh_from_context(self):
        """refresh_from_context"""
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
