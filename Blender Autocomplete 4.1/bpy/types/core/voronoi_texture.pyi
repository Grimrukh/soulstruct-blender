import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .texture import Texture

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VoronoiTexture(Texture, ID, bpy_struct):
    """Procedural voronoi texture"""

    color_mode: str
    """ 

    :type: str
    """

    distance_metric: str
    """ Algorithm used to calculate distance of sample points to feature points

    :type: str
    """

    minkovsky_exponent: float
    """ Minkowski exponent

    :type: float
    """

    nabla: float
    """ Size of derivative offset used for calculating normal

    :type: float
    """

    noise_intensity: float
    """ Scales the intensity of the noise

    :type: float
    """

    noise_scale: float
    """ Scaling for noise input

    :type: float
    """

    weight_1: float
    """ Voronoi feature weight 1

    :type: float
    """

    weight_2: float
    """ Voronoi feature weight 2

    :type: float
    """

    weight_3: float
    """ Voronoi feature weight 3

    :type: float
    """

    weight_4: float
    """ Voronoi feature weight 4

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
