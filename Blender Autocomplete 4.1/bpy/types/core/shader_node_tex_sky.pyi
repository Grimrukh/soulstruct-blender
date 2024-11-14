import typing
import collections.abc
import mathutils
from .color_mapping import ColorMapping
from .struct import Struct
from .shader_node import ShaderNode
from .bpy_struct import bpy_struct
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .tex_mapping import TexMapping
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderNodeTexSky(ShaderNode, NodeInternal, Node, bpy_struct):
    """Generate a procedural sky texture"""

    air_density: float
    """ Density of air molecules

    :type: float
    """

    altitude: float
    """ Height from sea level

    :type: float
    """

    color_mapping: ColorMapping
    """ Color mapping settings

    :type: ColorMapping
    """

    dust_density: float
    """ Density of dust molecules and water droplets

    :type: float
    """

    ground_albedo: float
    """ Ground color that is subtly reflected in the sky

    :type: float
    """

    ozone_density: float
    """ Density of ozone layer

    :type: float
    """

    sky_type: str
    """ Which sky model should be used

    :type: str
    """

    sun_direction: mathutils.Vector
    """ Direction from where the sun is shining

    :type: mathutils.Vector
    """

    sun_disc: bool
    """ Include the sun itself in the output

    :type: bool
    """

    sun_elevation: float
    """ Sun angle from horizon

    :type: float
    """

    sun_intensity: float
    """ Strength of sun

    :type: float
    """

    sun_rotation: float
    """ Rotation of sun around zenith

    :type: float
    """

    sun_size: float
    """ Size of sun disc

    :type: float
    """

    texture_mapping: TexMapping
    """ Texture coordinate mapping settings

    :type: TexMapping
    """

    turbidity: float
    """ Atmospheric turbidity

    :type: float
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
