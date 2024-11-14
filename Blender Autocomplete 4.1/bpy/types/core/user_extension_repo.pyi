import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UserExtensionRepo(bpy_struct):
    """Settings to define an extension repository"""

    custom_directory: str
    """ The local directory containing extensions

    :type: str
    """

    enabled: bool
    """ Enable the repository

    :type: bool
    """

    module: str
    """ Unique module identifier

    :type: str
    """

    name: str
    """ Unique repository name

    :type: str
    """

    remote_path: str
    """ Remote URL or path for extension repository

    :type: str
    """

    use_cache: bool
    """ Store packages in local cache, otherwise downloaded package files are immediately deleted after installation

    :type: bool
    """

    use_custom_directory: bool
    """ Manually set the path for extensions to be stored. When disabled a users extensions directory is created

    :type: bool
    """

    use_remote_path: bool
    """ Synchronize the repository with a remote URL/path

    :type: bool
    """

    directory: typing.Any
    """ Return directory or a default path derived from the users scripts path.(readonly)"""

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
