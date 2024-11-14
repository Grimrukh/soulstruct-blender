import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .user_extension_repo import UserExtensionRepo

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UserExtensionRepoCollection(bpy_prop_collection[UserExtensionRepo], bpy_struct):
    """Collection of user extension repositories"""

    @classmethod
    def new(
        cls,
        name: str | typing.Any = "",
        module: str | typing.Any = "",
        custom_directory: str | typing.Any = "",
        remote_path: str | typing.Any = "",
    ) -> UserExtensionRepo:
        """Add a new repository

        :param name: Name
        :type name: str | typing.Any
        :param module: Module
        :type module: str | typing.Any
        :param custom_directory: Custom Directory
        :type custom_directory: str | typing.Any
        :param remote_path: Remote Path
        :type remote_path: str | typing.Any
        :return: Newly added repository
        :rtype: UserExtensionRepo
        """
        ...

    @classmethod
    def remove(cls, repo: UserExtensionRepo):
        """Remove repos

        :param repo: Repository to remove
        :type repo: UserExtensionRepo
        """
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
