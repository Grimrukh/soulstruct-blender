import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .render_engine import RenderEngine

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class HydraRenderEngine(RenderEngine, bpy_struct):
    """Base class from USD Hydra based renderers"""

    def get_render_settings(self, engine_type):
        """Provide render settings for HdRenderDelegate.

        :param engine_type:
        """
        ...

    def render(self, depsgraph):
        """

        :param depsgraph:
        """
        ...

    def update(self, data, depsgraph):
        """

        :param data:
        :param depsgraph:
        """
        ...

    def view_draw(self, context, depsgraph):
        """

        :param context:
        :param depsgraph:
        """
        ...

    def view_update(self, context, depsgraph):
        """

        :param context:
        :param depsgraph:
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
