import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ParticleTarget(bpy_struct):
    """Target particle system"""

    alliance: str
    """ 

    :type: str
    """

    duration: float
    """ 

    :type: float
    """

    is_valid: bool
    """ Keyed particles target is valid

    :type: bool
    """

    name: str
    """ Particle target name

    :type: str
    """

    object: Object
    """ The object that has the target particle system (empty if same object)

    :type: Object
    """

    system: int
    """ The index of particle system on the target object

    :type: int
    """

    time: float
    """ 

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
