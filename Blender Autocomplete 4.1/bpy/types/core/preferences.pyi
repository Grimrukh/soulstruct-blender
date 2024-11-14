import typing
import collections.abc
import mathutils
from .preferences_view import PreferencesView
from .struct import Struct
from .preferences_edit import PreferencesEdit
from .bpy_prop_collection import bpy_prop_collection
from .preferences_input import PreferencesInput
from .studio_lights import StudioLights
from .theme_style import ThemeStyle
from .preferences_keymap import PreferencesKeymap
from .bpy_prop_array import bpy_prop_array
from .theme import Theme
from .preferences_system import PreferencesSystem
from .preferences_apps import PreferencesApps
from .bpy_struct import bpy_struct
from .preferences_experimental import PreferencesExperimental
from .preferences_file_paths import PreferencesFilePaths
from .path_compare_collection import PathCompareCollection
from .addons import Addons

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Preferences(bpy_struct):
    """Global preferences"""

    active_section: str | None
    """ Active section of the preferences shown in the user interface

    :type: str | None
    """

    addons: Addons
    """ 

    :type: Addons
    """

    app_template: str
    """ 

    :type: str
    """

    apps: PreferencesApps
    """ Preferences that work only for apps

    :type: PreferencesApps
    """

    autoexec_paths: PathCompareCollection
    """ 

    :type: PathCompareCollection
    """

    edit: PreferencesEdit
    """ Settings for interacting with Blender data

    :type: PreferencesEdit
    """

    experimental: PreferencesExperimental
    """ Settings for features that are still early in their development stage

    :type: PreferencesExperimental
    """

    filepaths: PreferencesFilePaths
    """ Default paths for external files

    :type: PreferencesFilePaths
    """

    inputs: PreferencesInput
    """ Settings for input devices

    :type: PreferencesInput
    """

    is_dirty: bool
    """ Preferences have changed

    :type: bool
    """

    keymap: PreferencesKeymap
    """ Shortcut setup for keyboards and other input devices

    :type: PreferencesKeymap
    """

    studio_lights: StudioLights
    """ 

    :type: StudioLights
    """

    system: PreferencesSystem
    """ Graphics driver and operating system settings

    :type: PreferencesSystem
    """

    themes: bpy_prop_collection[Theme]
    """ 

    :type: bpy_prop_collection[Theme]
    """

    ui_styles: bpy_prop_collection[ThemeStyle]
    """ 

    :type: bpy_prop_collection[ThemeStyle]
    """

    use_preferences_save: bool
    """ Save preferences on exit when modified (unless factory settings have been loaded)

    :type: bool
    """

    use_recent_searches: bool
    """ Sort the recently searched items at the top

    :type: bool
    """

    version: bpy_prop_array[int]
    """ Version of Blender the userpref.blend was saved with

    :type: bpy_prop_array[int]
    """

    view: PreferencesView
    """ Preferences related to viewing data

    :type: PreferencesView
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
