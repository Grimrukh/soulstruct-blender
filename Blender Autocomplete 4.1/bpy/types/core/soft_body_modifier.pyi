import typing
import collections.abc
import mathutils
from .struct import Struct
from .soft_body_settings import SoftBodySettings
from .bpy_struct import bpy_struct
from .point_cache import PointCache
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SoftBodyModifier(Modifier, bpy_struct):
    """Soft body simulation modifier"""

    point_cache: PointCache
    """ 

    :type: PointCache
    """

    settings: SoftBodySettings
    """ 

    :type: SoftBodySettings
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
