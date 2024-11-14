import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .scene_render_view import SceneRenderView
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RenderViews(bpy_prop_collection[SceneRenderView], bpy_struct):
    """Collection of render views"""

    active: SceneRenderView
    """ Active Render View

    :type: SceneRenderView
    """

    active_index: int | None
    """ Active index in render view array

    :type: int | None
    """

    def new(self, name: str | typing.Any) -> SceneRenderView:
        """Add a render view to scene

        :param name: New name for the marker (not unique)
        :type name: str | typing.Any
        :return: Newly created render view
        :rtype: SceneRenderView
        """
        ...

    def remove(self, view: SceneRenderView):
        """Remove a render view

        :param view: Render view to remove
        :type view: SceneRenderView
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
