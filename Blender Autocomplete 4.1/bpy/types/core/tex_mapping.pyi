import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TexMapping(bpy_struct):
    """Texture coordinate mapping settings"""

    mapping: str
    """ 

    :type: str
    """

    mapping_x: str
    """ 

    :type: str
    """

    mapping_y: str
    """ 

    :type: str
    """

    mapping_z: str
    """ 

    :type: str
    """

    max: mathutils.Vector
    """ Maximum value for clipping

    :type: mathutils.Vector
    """

    min: mathutils.Vector
    """ Minimum value for clipping

    :type: mathutils.Vector
    """

    rotation: mathutils.Euler
    """ 

    :type: mathutils.Euler
    """

    scale: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    translation: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    use_max: bool
    """ Whether to use maximum clipping value

    :type: bool
    """

    use_min: bool
    """ Whether to use minimum clipping value

    :type: bool
    """

    vector_type: str
    """ Type of vector that the mapping transforms

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
