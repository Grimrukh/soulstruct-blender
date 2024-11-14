import typing
import collections.abc
import mathutils
from .script_directory_collection import ScriptDirectoryCollection
from .struct import Struct
from .bpy_struct import bpy_struct
from .user_extension_repo_collection import UserExtensionRepoCollection
from .asset_library_collection import AssetLibraryCollection

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PreferencesFilePaths(bpy_struct):
    """Default paths for external files"""

    active_asset_library: int | None
    """ Index of the asset library being edited in the Preferences UI

    :type: int | None
    """

    active_extension_repo: int | None
    """ Index of the extensions repository being edited in the Preferences UI

    :type: int | None
    """

    animation_player: str
    """ Path to a custom animation/frame sequence player

    :type: str
    """

    animation_player_preset: str
    """ Preset configs for external animation players

    :type: str
    """

    asset_libraries: AssetLibraryCollection
    """ 

    :type: AssetLibraryCollection
    """

    auto_save_time: int
    """ The time (in minutes) to wait between automatic temporary saves

    :type: int
    """

    extension_repos: UserExtensionRepoCollection
    """ 

    :type: UserExtensionRepoCollection
    """

    file_preview_type: str
    """ What type of blend preview to create

    :type: str
    """

    font_directory: str
    """ The default directory to search for loading fonts

    :type: str
    """

    i18n_branches_directory: str
    """ The path to the '/branches' directory of your local svn-translation copy, to allow translating from the UI

    :type: str
    """

    image_editor: str
    """ Path to an image editor

    :type: str
    """

    recent_files: int
    """ Maximum number of recently opened files to remember

    :type: int
    """

    render_cache_directory: str
    """ Where to cache raw render results

    :type: str
    """

    render_output_directory: str
    """ The default directory for rendering output, for new scenes

    :type: str
    """

    save_version: int
    """ The number of old versions to maintain in the current directory, when manually saving

    :type: int
    """

    script_directories: ScriptDirectoryCollection
    """ 

    :type: ScriptDirectoryCollection
    """

    show_hidden_files_datablocks: bool
    """ Show files and data-blocks that are normally hidden

    :type: bool
    """

    show_recent_locations: bool
    """ Show Recent locations list in the File Browser

    :type: bool
    """

    show_system_bookmarks: bool
    """ Show System locations list in the File Browser

    :type: bool
    """

    sound_directory: str
    """ The default directory to search for sounds

    :type: str
    """

    temporary_directory: str
    """ The directory for storing temporary save files. The path must reference an existing directory or it will be ignored

    :type: str
    """

    text_editor: str
    """ Command to launch the text editor, either a full path or a command in $PATH.
Use the internal editor when left blank

    :type: str
    """

    text_editor_args: str
    """ Defines the specific format of the arguments with which the text editor opens files. The supported expansions are as follows:$filepath The absolute path of the file.
$line The line to open at (Optional).
$column The column to open from the beginning of the line (Optional).
$line0 & column0 start at zero.
Example: -f $filepath -l $line -c $column

    :type: str
    """

    texture_directory: str
    """ The default directory to search for textures

    :type: str
    """

    use_auto_save_temporary_files: bool
    """ Automatic saving of temporary files in temp directory, uses process ID.
Warning: Sculpt and edit mode data won't be saved

    :type: bool
    """

    use_file_compression: bool
    """ Enable file compression when saving .blend files

    :type: bool
    """

    use_filter_files: bool
    """ Enable filtering of files in the File Browser

    :type: bool
    """

    use_load_ui: bool
    """ Load user interface setup when loading .blend files

    :type: bool
    """

    use_relative_paths: bool
    """ Default relative path option for the file selector, when no path is defined yet

    :type: bool
    """

    use_scripts_auto_execute: bool
    """ Allow any .blend file to run scripts automatically (unsafe with blend files from an untrusted source)

    :type: bool
    """

    use_tabs_as_spaces: bool
    """ Automatically convert all new tabs into spaces for new and loaded text files

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
