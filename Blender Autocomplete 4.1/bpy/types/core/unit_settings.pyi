import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UnitSettings(bpy_struct):
    length_unit: str
    """ Unit that will be used to display length values

    :type: str
    """

    mass_unit: str
    """ Unit that will be used to display mass values

    :type: str
    """

    scale_length: float
    """ Scale to use when converting between Blender units and dimensions. When working at microscopic or astronomical scale, a small or large unit scale respectively can be used to avoid numerical precision problems

    :type: float
    """

    system: str
    """ The unit system to use for user interface controls

    :type: str
    """

    system_rotation: str
    """ Unit to use for displaying/editing rotation values

    :type: str
    """

    temperature_unit: str
    """ Unit that will be used to display temperature values

    :type: str
    """

    time_unit: str
    """ Unit that will be used to display time values

    :type: str
    """

    use_separate: bool
    """ Display units in pairs (e.g. 1m 0cm)

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
