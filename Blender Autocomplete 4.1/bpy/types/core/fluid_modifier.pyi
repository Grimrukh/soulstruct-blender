import typing
import collections.abc
import mathutils
from .fluid_flow_settings import FluidFlowSettings
from .fluid_effector_settings import FluidEffectorSettings
from .fluid_domain_settings import FluidDomainSettings
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FluidModifier(Modifier, bpy_struct):
    """Fluid simulation modifier"""

    domain_settings: FluidDomainSettings
    """ 

    :type: FluidDomainSettings
    """

    effector_settings: FluidEffectorSettings
    """ 

    :type: FluidEffectorSettings
    """

    flow_settings: FluidFlowSettings
    """ 

    :type: FluidFlowSettings
    """

    fluid_type: str
    """ 

    :type: str
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
