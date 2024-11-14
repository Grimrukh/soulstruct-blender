import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .depsgraph_object_instance import DepsgraphObjectInstance
from .bpy_struct import bpy_struct
from .depsgraph_update import DepsgraphUpdate
from .id import ID
from .object import Object
from .view_layer import ViewLayer
from .scene import Scene

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Depsgraph(bpy_struct):
    ids: bpy_prop_collection[ID]
    """ All evaluated data-blocks

    :type: bpy_prop_collection[ID]
    """

    mode: str
    """ Evaluation mode

    :type: str
    """

    object_instances: bpy_prop_collection[DepsgraphObjectInstance]
    """ All object instances to display or render (Warning: Only use this as an iterator, never as a sequence, and do not keep any references to its items)

    :type: bpy_prop_collection[DepsgraphObjectInstance]
    """

    objects: bpy_prop_collection[Object]
    """ Evaluated objects in the dependency graph

    :type: bpy_prop_collection[Object]
    """

    scene: Scene
    """ Original scene dependency graph is built for

    :type: Scene
    """

    scene_eval: Scene
    """ Scene at its evaluated state

    :type: Scene
    """

    updates: bpy_prop_collection[DepsgraphUpdate]
    """ Updates to data-blocks

    :type: bpy_prop_collection[DepsgraphUpdate]
    """

    view_layer: ViewLayer
    """ Original view layer dependency graph is built for

    :type: ViewLayer
    """

    view_layer_eval: ViewLayer
    """ View layer at its evaluated state

    :type: ViewLayer
    """

    def debug_relations_graphviz(self, filepath: str | typing.Any):
        """debug_relations_graphviz

        :param filepath: File Name, Output path for the graphviz debug file
        :type filepath: str | typing.Any
        """
        ...

    def debug_stats_gnuplot(
        self, filepath: str | typing.Any, output_filepath: str | typing.Any
    ):
        """debug_stats_gnuplot

        :param filepath: File Name, Output path for the gnuplot debug file
        :type filepath: str | typing.Any
        :param output_filepath: Output File Name, File name where gnuplot script will save the result
        :type output_filepath: str | typing.Any
        """
        ...

    def debug_tag_update(self):
        """debug_tag_update"""
        ...

    def debug_stats(self) -> str | typing.Any:
        """Report the number of elements in the Dependency Graph

        :return: result
        :rtype: str | typing.Any
        """
        ...

    def update(self):
        """Re-evaluate any modified data-blocks, for example for animation or modifiers. This invalidates all references to evaluated data-blocks from this dependency graph."""
        ...

    def id_eval_get(self, id: ID | None) -> ID:
        """id_eval_get

        :param id: Original ID to get evaluated complementary part for
        :type id: ID | None
        :return: Evaluated ID for the given original one
        :rtype: ID
        """
        ...

    def id_type_updated(self, id_type: str | None) -> bool:
        """id_type_updated

        :param id_type: ID Type
        :type id_type: str | None
        :return: Updated, True if any datablock with this type was added, updated or removed
        :rtype: bool
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
