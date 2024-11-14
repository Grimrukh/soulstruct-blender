import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MetaElement(bpy_struct):
    """Blobby element in a metaball data-block"""

    co: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    hide: bool
    """ Hide element

    :type: bool
    """

    radius: float
    """ 

    :type: float
    """

    rotation: mathutils.Quaternion
    """ Normalized quaternion rotation

    :type: mathutils.Quaternion
    """

    select: bool
    """ Select element

    :type: bool
    """

    size_x: float
    """ Size of element, use of components depends on element type

    :type: float
    """

    size_y: float
    """ Size of element, use of components depends on element type

    :type: float
    """

    size_z: float
    """ Size of element, use of components depends on element type

    :type: float
    """

    stiffness: float
    """ Stiffness defines how much of the element to fill

    :type: float
    """

    type: str
    """ Metaball type

    :type: str
    """

    use_negative: bool
    """ Set metaball as negative one

    :type: bool
    """

    use_scale_stiffness: bool
    """ Scale stiffness instead of radius

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
