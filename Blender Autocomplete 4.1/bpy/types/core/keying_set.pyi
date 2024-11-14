import typing
import collections.abc
import mathutils
from .keying_set_info import KeyingSetInfo
from .struct import Struct
from .keying_set_paths import KeyingSetPaths
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyingSet(bpy_struct):
    """Settings that should be keyframed together"""

    bl_description: str
    """ A short description of the keying set

    :type: str
    """

    bl_idname: str
    """ If this is set, the Keying Set gets a custom ID, otherwise it takes the name of the class used to define the Keying Set (for example, if the class name is "BUILTIN_KSI_location", and bl_idname is not set by the script, then bl_idname = "BUILTIN_KSI_location")

    :type: str
    """

    bl_label: str
    """ 

    :type: str
    """

    is_path_absolute: bool
    """ Keying Set defines specific paths/settings to be keyframed (i.e. is not reliant on context info)

    :type: bool
    """

    paths: KeyingSetPaths
    """ Keying Set Paths to define settings that get keyframed together

    :type: KeyingSetPaths
    """

    type_info: KeyingSetInfo
    """ Callback function defines for built-in Keying Sets

    :type: KeyingSetInfo
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

    def refresh(self):
        """Refresh Keying Set to ensure that it is valid for the current context (call before each use of one)"""
        ...

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
