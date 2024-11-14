import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BuildModifier(Modifier, bpy_struct):
    """Build effect modifier"""

    frame_duration: float
    """ Total time the build effect requires

    :type: float
    """

    frame_start: float
    """ Start frame of the effect

    :type: float
    """

    seed: int
    """ Seed for random if used

    :type: int
    """

    use_random_order: bool
    """ Randomize the faces or edges during build

    :type: bool
    """

    use_reverse: bool
    """ Deconstruct the mesh instead of building it

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
