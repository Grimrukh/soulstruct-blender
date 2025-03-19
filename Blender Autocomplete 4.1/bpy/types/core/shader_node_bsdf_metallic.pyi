import typing
import collections.abc
import mathutils
from .struct import Struct
from .shader_node import ShaderNode
from .bpy_struct import bpy_struct
from .node_internal_socket_template import NodeInternalSocketTemplate
from .node import Node
from .node_internal import NodeInternal

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderNodeBsdfMetallic(ShaderNode, NodeInternal, Node, bpy_struct):
    """Metallic reflection with microfacet distribution, and metallic fresnel"""

    distribution: str = "BECKMANN"
    """ Light scattering distribution on rough surface

    :type: str
        BECKMANN - Beckmann.
        GGX - GGX.
        MULTI_GGX - Multiscatter GGX – GGX with additional correction to account for multiple scattering, preserve 
            energy and prevent unexpected darkening at high roughness.
    """

    fresnel_type: str = "PHYSICAL_CONDUCTOR"
    """ Fresnel method used to tint the metal

    :type: str
        PHYSICAL_CONDUCTOR - Physical Conductor – Fresnel conductor based on the complex refractive index per color 
            channel.
        F82 - F82 Tint – An approximation of the Fresnel conductor curve based on the colors at perpendicular and 
            near-grazing (roughly 82°) angles.
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
