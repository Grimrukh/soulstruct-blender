import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyingSetPath(bpy_struct):
    """Path to a setting for use in a Keying Set"""

    array_index: int
    """ Index to the specific setting if applicable

    :type: int
    """

    data_path: str
    """ Path to property setting

    :type: str
    """

    group: str
    """ Name of Action Group to assign setting(s) for this path to

    :type: str
    """

    group_method: str
    """ Method used to define which Group-name to use

    :type: str
    """

    id: ID
    """ ID-Block that keyframes for Keying Set should be added to (for Absolute Keying Sets only)

    :type: ID
    """

    id_type: str
    """ Type of ID-block that can be used

    :type: str
    """

    use_entire_array: bool
    """ When an 'array/vector' type is chosen (Location, Rotation, Color, etc.), entire array is to be used

    :type: bool
    """

    use_insertkey_needed: bool
    """ Only insert keyframes where they're needed in the relevant F-Curves

    :type: bool
    """

    use_insertkey_override_needed: bool
    """ Override default setting to only insert keyframes where they're needed in the relevant F-Curves

    :type: bool
    """

    use_insertkey_override_visual: bool
    """ Override default setting to insert keyframes based on 'visual transforms'

    :type: bool
    """

    use_insertkey_visual: bool
    """ Insert keyframes based on 'visual transforms'

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
