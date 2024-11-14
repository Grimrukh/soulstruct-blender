import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .key_config_preferences import KeyConfigPreferences
from .key_maps import KeyMaps

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyConfig(bpy_struct):
    """Input configuration, including keymaps"""

    is_user_defined: bool
    """ Indicates that a keyconfig was defined by the user

    :type: bool
    """

    keymaps: KeyMaps
    """ Key maps configured as part of this configuration

    :type: KeyMaps
    """

    name: str
    """ Name of the key configuration

    :type: str
    """

    preferences: KeyConfigPreferences
    """ 

    :type: KeyConfigPreferences
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
