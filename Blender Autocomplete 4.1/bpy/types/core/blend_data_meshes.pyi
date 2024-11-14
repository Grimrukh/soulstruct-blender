import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .mesh import Mesh
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .depsgraph import Depsgraph

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataMeshes(bpy_prop_collection[Mesh], bpy_struct):
    """Collection of meshes"""

    def new(self, name: str | typing.Any) -> Mesh:
        """Add a new mesh to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New mesh data-block
        :rtype: Mesh
        """
        ...

    def new_from_object(
        self,
        object: Object,
        preserve_all_data_layers: bool | typing.Any | None = False,
        depsgraph: Depsgraph | None = None,
    ) -> Mesh:
        """Add a new mesh created from given object (undeformed geometry if object is original, and final evaluated geometry, with all modifiers etc., if object is evaluated)

        :param object: Object to create mesh from
        :type object: Object
        :param preserve_all_data_layers: Preserve all data layers in the mesh, like UV maps and vertex groups. By default Blender only computes the subset of data layers needed for viewport display and rendering, for better performance
        :type preserve_all_data_layers: bool | typing.Any | None
        :param depsgraph: Dependency Graph, Evaluated dependency graph which is required when preserve_all_data_layers is true
        :type depsgraph: Depsgraph | None
        :return: Mesh created from object, remove it if it is only used for export
        :rtype: Mesh
        """
        ...

    def remove(
        self,
        mesh: Mesh,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a mesh from the current blendfile

        :param mesh: Mesh to remove
        :type mesh: Mesh
        :param do_unlink: Unlink all usages of this mesh before deleting it (WARNING: will also delete objects instancing that mesh data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this mesh data
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this mesh data
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
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
