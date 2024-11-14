import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .library import Library

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataLibraries(bpy_prop_collection[Library], bpy_struct):
    """Collection of libraries"""

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
        """
        ...

    def remove(
        self,
        library: Library,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a library from the current blendfile

        :param library: Library to remove
        :type library: Library
        :param do_unlink: Unlink all usages of this library before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this library
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this library
        :type do_ui_user: bool | typing.Any | None
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

    def load(
        self,
        filepath: bytes | str | None,
        link: bool | None = False,
        relative: bool | None = False,
        assets_only: bool | None = False,
        create_liboverrides: bool | None = False,
        reuse_liboverrides: bool | None = False,
        create_liboverrides_runtime: bool | None = False,
    ):
        """Returns a context manager which exposes 2 library objects on entering.
        Each object has attributes matching bpy.data which are lists of strings to be linked.

                :param filepath: The path to a blend file.
                :type filepath: bytes | str | None
                :param link: When False reference to the original file is lost.
                :type link: bool | None
                :param relative: When True the path is stored relative to the open blend file.
                :type relative: bool | None
                :param assets_only: If True, only list data-blocks marked as assets.
                :type assets_only: bool | None
                :param create_liboverrides: If True and link is True, liboverrides will
        be created for linked data.
                :type create_liboverrides: bool | None
                :param reuse_liboverrides: If True and create_liboverride is True,
        search for existing liboverride first.
                :type reuse_liboverrides: bool | None
                :param create_liboverrides_runtime: If True and create_liboverride is True,
        create (or search for existing) runtime liboverride.
                :type create_liboverrides_runtime: bool | None
        """
        ...

    def write(
        self,
        filepath: bytes | str | None,
        datablocks: set | None,
        path_remap: str | None = False,
        fake_user: bool | None = False,
        compress: bool | None = False,
    ):
        """Write data-blocks into a blend file.

                :param filepath: The path to write the blend-file.
                :type filepath: bytes | str | None
                :param datablocks: set of data-blocks (`bpy.types.ID` instances).
                :type datablocks: set | None
                :param path_remap: Optionally remap paths when writing the file:

        NONE No path manipulation (default).

        RELATIVE Remap paths that are already relative to the new location.

        RELATIVE_ALL Remap all paths to be relative to the new location.

        ABSOLUTE Make all paths absolute on writing.
                :type path_remap: str | None
                :param fake_user: When True, data-blocks will be written with fake-user flag enabled.
                :type fake_user: bool | None
                :param compress: When True, write a compressed blend file.
                :type compress: bool | None
        """
        ...
