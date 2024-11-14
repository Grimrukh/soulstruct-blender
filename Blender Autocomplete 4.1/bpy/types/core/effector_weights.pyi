import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class EffectorWeights(bpy_struct):
    """Effector weights for physics simulation"""

    all: float
    """ All effector's weight

    :type: float
    """

    apply_to_hair_growing: bool
    """ Use force fields when growing hair

    :type: bool
    """

    boid: float
    """ Boid effector weight

    :type: float
    """

    charge: float
    """ Charge effector weight

    :type: float
    """

    collection: Collection
    """ Limit effectors to this collection

    :type: Collection
    """

    curve_guide: float
    """ Curve guide effector weight

    :type: float
    """

    drag: float
    """ Drag effector weight

    :type: float
    """

    force: float
    """ Force effector weight

    :type: float
    """

    gravity: float
    """ Global gravity weight

    :type: float
    """

    harmonic: float
    """ Harmonic effector weight

    :type: float
    """

    lennardjones: float
    """ Lennard-Jones effector weight

    :type: float
    """

    magnetic: float
    """ Magnetic effector weight

    :type: float
    """

    smokeflow: float
    """ Fluid Flow effector weight

    :type: float
    """

    texture: float
    """ Texture effector weight

    :type: float
    """

    turbulence: float
    """ Turbulence effector weight

    :type: float
    """

    vortex: float
    """ Vortex effector weight

    :type: float
    """

    wind: float
    """ Wind effector weight

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
