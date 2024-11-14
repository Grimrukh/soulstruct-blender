import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WorldMistSettings(bpy_struct):
    """Mist settings for a World data-block"""

    depth: float
    """ Distance over which the mist effect fades in

    :type: float
    """

    falloff: str
    """ Type of transition used to fade mist

    :type: str
    """

    height: float
    """ Control how much mist density decreases with height

    :type: float
    """

    intensity: float
    """ Overall minimum intensity of the mist effect

    :type: float
    """

    start: float
    """ Starting distance of the mist, measured from the camera

    :type: float
    """

    use_mist: bool
    """ Occlude objects with the environment color as they are further away

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
