import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .mesh_loop_color_layer import MeshLoopColorLayer
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LoopColors(bpy_prop_collection[MeshLoopColorLayer], bpy_struct):
    """Collection of vertex colors"""

    active: MeshLoopColorLayer | None
    """ Active vertex color layer

    :type: MeshLoopColorLayer | None
    """

    active_index: int | None
    """ Active vertex color index

    :type: int | None
    """

    def new(
        self, name: str | typing.Any = "Col", do_init: bool | typing.Any | None = True
    ) -> MeshLoopColorLayer:
        """Add a vertex color layer to Mesh

        :param name: Vertex color name
        :type name: str | typing.Any
        :param do_init: Whether new layer's data should be initialized by copying current active one
        :type do_init: bool | typing.Any | None
        :return: The newly created layer
        :rtype: MeshLoopColorLayer
        """
        ...

    def remove(self, layer: MeshLoopColorLayer):
        """Remove a vertex color layer

        :param layer: The layer to remove
        :type layer: MeshLoopColorLayer
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
