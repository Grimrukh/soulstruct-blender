import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .file_select_id_filter import FileSelectIDFilter

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FileSelectParams(bpy_struct):
    """File Select Parameters"""

    directory: str
    """ Directory displayed in the file browser

    :type: str
    """

    display_size: int
    """ Change the size of thumbnails

    :type: int
    """

    display_size_discrete: str
    """ Change the size of thumbnails in discrete steps

    :type: str
    """

    display_type: str
    """ Display mode for the file list

    :type: str
    """

    filename: str
    """ Active file in the file browser

    :type: str
    """

    filter_glob: str
    """ UNIX shell-like filename patterns matching, supports wildcards ('*') and list of patterns separated by ';'

    :type: str
    """

    filter_id: FileSelectIDFilter
    """ Which ID types to show/hide, when browsing a library

    :type: FileSelectIDFilter
    """

    filter_search: str
    """ Filter by name or tag, supports '*' wildcard

    :type: str
    """

    recursion_level: str
    """ Numbers of dirtree levels to show simultaneously

    :type: str
    """

    show_details_datetime: bool
    """ Show a column listing the date and time of modification for each file

    :type: bool
    """

    show_details_size: bool
    """ Show a column listing the size of each file

    :type: bool
    """

    show_hidden: bool
    """ Show hidden dot files

    :type: bool
    """

    sort_method: str
    """ 

    :type: str
    """

    title: str
    """ Title for the file browser

    :type: str
    """

    use_filter: bool
    """ Enable filtering of files

    :type: bool
    """

    use_filter_asset_only: bool
    """ Hide .blend files items that are not data-blocks with asset metadata

    :type: bool
    """

    use_filter_backup: bool
    """ Show .blend1, .blend2, etc. files

    :type: bool
    """

    use_filter_blender: bool
    """ Show .blend files

    :type: bool
    """

    use_filter_blendid: bool
    """ Show .blend files items (objects, materials, etc.)

    :type: bool
    """

    use_filter_folder: bool
    """ Show folders

    :type: bool
    """

    use_filter_font: bool
    """ Show font files

    :type: bool
    """

    use_filter_image: bool
    """ Show image files

    :type: bool
    """

    use_filter_movie: bool
    """ Show movie files

    :type: bool
    """

    use_filter_script: bool
    """ Show script files

    :type: bool
    """

    use_filter_sound: bool
    """ Show sound files

    :type: bool
    """

    use_filter_text: bool
    """ Show text files

    :type: bool
    """

    use_filter_volume: bool
    """ Show 3D volume files

    :type: bool
    """

    use_library_browsing: bool
    """ Whether we may browse Blender files' content or not

    :type: bool
    """

    use_sort_invert: bool
    """ Sort items descending, from highest value to lowest

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
