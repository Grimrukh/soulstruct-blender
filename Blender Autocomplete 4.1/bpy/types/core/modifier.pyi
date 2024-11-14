import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Modifier(bpy_struct):
    """Modifier affecting the geometry data of an object"""

    execution_time: float
    """ Time in seconds that the modifier took to evaluate. This is only set on evaluated objects. If multiple modifiers run in parallel, execution time is not a reliable metric

    :type: float
    """

    is_active: bool
    """ The active modifier in the list

    :type: bool
    """

    is_override_data: bool
    """ In a local override object, whether this modifier comes from the linked reference object, or is local to the override

    :type: bool
    """

    name: str
    """ Modifier name

    :type: str
    """

    persistent_uid: int
    """ Uniquely identifies the modifier within the modifier stack that it is part of

    :type: int
    """

    show_expanded: bool
    """ Set modifier expanded in the user interface

    :type: bool
    """

    show_in_editmode: bool
    """ Display modifier in Edit mode

    :type: bool
    """

    show_on_cage: bool
    """ Adjust edit cage to modifier result

    :type: bool
    """

    show_render: bool
    """ Use modifier during render

    :type: bool
    """

    show_viewport: bool
    """ Display modifier in viewport

    :type: bool
    """

    type: str
    """ 

    :type: str
    """

    use_apply_on_spline: bool
    """ Apply this and all preceding deformation modifiers on splines' points rather than on filled curve/surface

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
