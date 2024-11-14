import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .world_mist_settings import WorldMistSettings
from .anim_data import AnimData
from .id import ID
from .world_lighting import WorldLighting
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class World(ID, bpy_struct):
    """World data-block describing the environment and ambient lighting of a scene"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    color: mathutils.Color
    """ Color of the background

    :type: mathutils.Color
    """

    cycles: typing.Any
    """ Cycles world settings

    :type: typing.Any
    """

    cycles_visibility: typing.Any
    """ Cycles visibility settings

    :type: typing.Any
    """

    light_settings: WorldLighting
    """ World lighting settings

    :type: WorldLighting
    """

    lightgroup: str
    """ Lightgroup that the world belongs to

    :type: str
    """

    mist_settings: WorldMistSettings
    """ World mist settings

    :type: WorldMistSettings
    """

    node_tree: NodeTree
    """ Node tree for node based worlds

    :type: NodeTree
    """

    probe_resolution: str
    """ Resolution when baked to a texture

    :type: str
    """

    use_nodes: bool
    """ Use shader nodes to render the world

    :type: bool
    """

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
