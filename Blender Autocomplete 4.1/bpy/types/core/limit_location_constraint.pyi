import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LimitLocationConstraint(Constraint, bpy_struct):
    """Limit the location of the constrained object"""

    max_x: float
    """ Highest X value to allow

    :type: float
    """

    max_y: float
    """ Highest Y value to allow

    :type: float
    """

    max_z: float
    """ Highest Z value to allow

    :type: float
    """

    min_x: float
    """ Lowest X value to allow

    :type: float
    """

    min_y: float
    """ Lowest Y value to allow

    :type: float
    """

    min_z: float
    """ Lowest Z value to allow

    :type: float
    """

    use_max_x: bool
    """ Use the maximum X value

    :type: bool
    """

    use_max_y: bool
    """ Use the maximum Y value

    :type: bool
    """

    use_max_z: bool
    """ Use the maximum Z value

    :type: bool
    """

    use_min_x: bool
    """ Use the minimum X value

    :type: bool
    """

    use_min_y: bool
    """ Use the minimum Y value

    :type: bool
    """

    use_min_z: bool
    """ Use the minimum Z value

    :type: bool
    """

    use_transform_limit: bool
    """ Transform tools are affected by this constraint as well

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
