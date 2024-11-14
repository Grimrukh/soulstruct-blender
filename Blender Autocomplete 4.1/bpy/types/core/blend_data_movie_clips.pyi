import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_clip import MovieClip

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataMovieClips(bpy_prop_collection[MovieClip], bpy_struct):
    """Collection of movie clips"""

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
        """
        ...

    def remove(
        self,
        clip: MovieClip,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a movie clip from the current blendfile.

        :param clip: Movie clip to remove
        :type clip: MovieClip
        :param do_unlink: Unlink all usages of this movie clip before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this movie clip
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this movie clip
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def load(
        self,
        filepath: str | typing.Any,
        check_existing: bool | typing.Any | None = False,
    ) -> MovieClip:
        """Add a new movie clip to the main database from a file (while check_existing is disabled for consistency with other load functions, behavior with multiple movie-clips using the same file may incorrectly generate proxies)

        :param filepath: path for the data-block
        :type filepath: str | typing.Any
        :param check_existing: Using existing data-block if this file is already loaded
        :type check_existing: bool | typing.Any | None
        :return: New movie clip data-block
        :rtype: MovieClip
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
