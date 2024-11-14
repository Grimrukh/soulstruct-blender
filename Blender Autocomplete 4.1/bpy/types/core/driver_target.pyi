import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DriverTarget(bpy_struct):
    """Source of input values for driver variables"""

    bone_target: str
    """ Name of PoseBone to use as target

    :type: str
    """

    context_property: str
    """ Type of a context-dependent data-block to access property from

    :type: str
    """

    data_path: str
    """ RNA Path (from ID-block) to property used

    :type: str
    """

    fallback_value: float
    """ The value to use if the data path can't be resolved

    :type: float
    """

    id: ID
    """ ID-block that the specific property used can be found from (id_type property must be set first)

    :type: ID
    """

    id_type: str
    """ Type of ID-block that can be used

    :type: str
    """

    is_fallback_used: bool
    """ Indicates that the most recent variable evaluation used the fallback value

    :type: bool
    """

    rotation_mode: str
    """ Mode for calculating rotation channel values

    :type: str
    """

    transform_space: str
    """ Space in which transforms are used

    :type: str
    """

    transform_type: str
    """ Driver variable type

    :type: str
    """

    use_fallback_value: bool
    """ Use the fallback value if the data path can't be resolved, instead of failing to evaluate the driver

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
