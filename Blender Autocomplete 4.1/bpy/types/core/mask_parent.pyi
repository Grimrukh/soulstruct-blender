import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaskParent(bpy_struct):
    """Parenting settings for masking element"""

    id: ID
    """ ID-block to which masking element would be parented to or to its property

    :type: ID
    """

    id_type: str
    """ Type of ID-block that can be used

    :type: str
    """

    parent: str
    """ Name of parent object in specified data-block to which parenting happens

    :type: str
    """

    sub_parent: str
    """ Name of parent sub-object in specified data-block to which parenting happens

    :type: str
    """

    type: str
    """ Parent Type

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
