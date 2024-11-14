import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .texture import Texture

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MarbleTexture(Texture, ID, bpy_struct):
    """Procedural noise texture"""

    marble_type: str
    """ 

    :type: str
    """

    nabla: float
    """ Size of derivative offset used for calculating normal

    :type: float
    """

    noise_basis: str
    """ Noise basis used for turbulence

    :type: str
    """

    noise_basis_2: str
    """ 

    :type: str
    """

    noise_depth: int
    """ Depth of the cloud calculation

    :type: int
    """

    noise_scale: float
    """ Scaling for noise input

    :type: float
    """

    noise_type: str
    """ 

    :type: str
    """

    turbulence: float
    """ Turbulence of the bandnoise and ringnoise types

    :type: float
    """

    users_material: typing.Any
    """ Materials that use this texture(readonly)"""

    users_object_modifier: typing.Any
    """ Object modifiers that use this texture(readonly)"""

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
