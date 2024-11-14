import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .render_pass import RenderPass

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RenderPasses(bpy_prop_collection[RenderPass], bpy_struct):
    """Collection of render passes"""

    def find_by_type(self, pass_type: str | None, view: str | typing.Any) -> RenderPass:
        """Get the render pass for a given type and view

        :param pass_type: Pass
        :type pass_type: str | None
        :param view: View, Render view to get pass from
        :type view: str | typing.Any
        :return: The matching render pass
        :rtype: RenderPass
        """
        ...

    def find_by_name(
        self, name: str | typing.Any, view: str | typing.Any
    ) -> RenderPass:
        """Get the render pass for a given name and view

        :param name: Pass
        :type name: str | typing.Any
        :param view: View, Render view to get pass from
        :type view: str | typing.Any
        :return: The matching render pass
        :rtype: RenderPass
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
