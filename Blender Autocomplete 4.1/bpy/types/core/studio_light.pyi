import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .user_solid_light import UserSolidLight
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class StudioLight(bpy_struct):
    """Studio light"""

    has_specular_highlight_pass: bool
    """ Studio light image file has separate "diffuse" and "specular" passes

    :type: bool
    """

    index: int
    """ 

    :type: int
    """

    is_user_defined: bool
    """ 

    :type: bool
    """

    light_ambient: mathutils.Color
    """ Color of the ambient light that uniformly lit the scene

    :type: mathutils.Color
    """

    name: str
    """ 

    :type: str
    """

    path: str
    """ 

    :type: str
    """

    solid_lights: bpy_prop_collection[UserSolidLight]
    """ Lights used to display objects in solid draw mode

    :type: bpy_prop_collection[UserSolidLight]
    """

    type: str
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
