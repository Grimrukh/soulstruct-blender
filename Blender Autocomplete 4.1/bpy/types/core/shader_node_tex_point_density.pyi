import typing
import collections.abc
import mathutils
from .struct import Struct
from .shader_node import ShaderNode
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .particle_system import ParticleSystem
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .object import Object
from .depsgraph import Depsgraph
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderNodeTexPointDensity(ShaderNode, NodeInternal, Node, bpy_struct):
    """Generate a volumetric point for each particle or vertex of another object"""

    interpolation: str
    """ Texture interpolation

    :type: str
    """

    object: Object
    """ Object to take point data from

    :type: Object
    """

    particle_color_source: str
    """ Data to derive color results from

    :type: str
    """

    particle_system: ParticleSystem
    """ Particle System to render as points

    :type: ParticleSystem
    """

    point_source: str
    """ Point data to use as renderable point density

    :type: str
    """

    radius: float
    """ Radius from the shaded sample to look for points within

    :type: float
    """

    resolution: int
    """ Resolution used by the texture holding the point density

    :type: int
    """

    space: str
    """ Coordinate system to calculate voxels in

    :type: str
    """

    vertex_attribute_name: str
    """ Vertex attribute to use for color

    :type: str
    """

    vertex_color_source: str
    """ Data to derive color results from

    :type: str
    """

    @classmethod
    def is_registered_node_type(cls) -> bool:
        """True if a registered node type

        :return: Result
        :rtype: bool
        """
        ...

    @classmethod
    def input_template(cls, index: int | None) -> NodeInternalSocketTemplate:
        """Input socket template

        :param index: Index
        :type index: int | None
        :return: result
        :rtype: NodeInternalSocketTemplate
        """
        ...

    @classmethod
    def output_template(cls, index: int | None) -> NodeInternalSocketTemplate:
        """Output socket template

        :param index: Index
        :type index: int | None
        :return: result
        :rtype: NodeInternalSocketTemplate
        """
        ...

    def cache_point_density(self, depsgraph: Depsgraph | None = None):
        """Cache point density data for later calculation

        :param depsgraph:
        :type depsgraph: Depsgraph | None
        """
        ...

    def calc_point_density(
        self, depsgraph: Depsgraph | None = None
    ) -> bpy_prop_array[float]:
        """Calculate point density

        :param depsgraph:
        :type depsgraph: Depsgraph | None
        :return: RGBA Values
        :rtype: bpy_prop_array[float]
        """
        ...

    def calc_point_density_minmax(self, depsgraph: Depsgraph | None = None):
        """Calculate point density

                :param depsgraph:
                :type depsgraph: Depsgraph | None
                :return: min, min, `mathutils.Vector` of 3 items in [-inf, inf]

        max, max, `mathutils.Vector` of 3 items in [-inf, inf]
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
