import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .anim_data import AnimData
from .id import ID
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Light(ID, bpy_struct):
    """Light data-block for lighting a scene"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    color: mathutils.Color
    """ Light color

    :type: mathutils.Color
    """

    cutoff_distance: float
    """ Distance at which the light influence will be set to 0

    :type: float
    """

    cycles: typing.Any
    """ Cycles light settings

    :type: typing.Any
    """

    diffuse_factor: float
    """ Diffuse reflection multiplier

    :type: float
    """

    node_tree: NodeTree
    """ Node tree for node based lights

    :type: NodeTree
    """

    specular_factor: float
    """ Specular reflection multiplier

    :type: float
    """

    type: str
    """ Type of light

    :type: str
    """

    use_custom_distance: bool
    """ Use custom attenuation distance instead of global light threshold

    :type: bool
    """

    use_nodes: bool
    """ Use shader nodes to render the light

    :type: bool
    """

    volume_factor: float
    """ Volume light multiplier

    :type: float
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
