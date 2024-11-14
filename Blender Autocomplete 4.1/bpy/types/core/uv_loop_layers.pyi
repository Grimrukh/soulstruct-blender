import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .mesh_uv_loop_layer import MeshUVLoopLayer

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UVLoopLayers(bpy_prop_collection[MeshUVLoopLayer], bpy_struct):
    """Collection of UV map layers"""

    active: MeshUVLoopLayer | None
    """ Active UV Map layer

    :type: MeshUVLoopLayer | None
    """

    active_index: int | None
    """ Active UV map index

    :type: int | None
    """

    def new(
        self, name: str | typing.Any = "UVMap", do_init: bool | typing.Any | None = True
    ) -> MeshUVLoopLayer:
        """Add a UV map layer to Mesh

        :param name: UV map name
        :type name: str | typing.Any
        :param do_init: Whether new layer's data should be initialized by copying current active one, or if none is active, with a default UVmap
        :type do_init: bool | typing.Any | None
        :return: The newly created layer
        :rtype: MeshUVLoopLayer
        """
        ...

    def remove(self, layer: MeshUVLoopLayer):
        """Remove a vertex color layer

        :param layer: The layer to remove
        :type layer: MeshUVLoopLayer
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
