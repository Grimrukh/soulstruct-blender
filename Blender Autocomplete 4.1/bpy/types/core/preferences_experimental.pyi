import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PreferencesExperimental(bpy_struct):
    """Experimental features"""

    enable_overlay_next: bool
    """ Enable the new Overlay codebase, requires restart

    :type: bool
    """

    override_auto_resync: bool
    """ Disable library overrides automatic resync detection and process on file load (can be useful to help fixing broken files)

    :type: bool
    """

    show_asset_debug_info: bool
    """ Enable some extra fields in the Asset Browser to aid in debugging

    :type: bool
    """

    use_all_linked_data_direct: bool
    """ Forces all linked data to be considered as directly linked. Workaround for current issues/limitations in BAT (Blender studio pipeline tool)

    :type: bool
    """

    use_asset_indexing: bool
    """ Disable the asset indexer, to force every asset library refresh to completely reread assets from disk

    :type: bool
    """

    use_cycles_debug: bool
    """ Enable Cycles debugging options for developers

    :type: bool
    """

    use_eevee_debug: bool
    """ Enable EEVEE debugging options for developers

    :type: bool
    """

    use_experimental_compositors: bool
    """ Enable compositor full frame and realtime GPU execution mode options (no tiling, reduces execution time and memory usage)

    :type: bool
    """

    use_extended_asset_browser: bool
    """ Enable Asset Browser editor and operators to manage regular data-blocks as assets, not just poses

    :type: bool
    """

    use_extension_repos: bool
    """ Enables extension repositories, accessible from the "Extension Repositories" panel in the "File Paths" section of the preferences. These paths are exposed as add-ons, package management is not yet integrated

    :type: bool
    """

    use_grease_pencil_version3: bool
    """ Enable the new grease pencil 3.0 codebase

    :type: bool
    """

    use_new_curves_tools: bool
    """ Enable additional features for the new curves data block

    :type: bool
    """

    use_new_point_cloud_type: bool
    """ Enable the new point cloud type in the ui

    :type: bool
    """

    use_new_volume_nodes: bool
    """ Enables visibility of the new Volume nodes in the UI

    :type: bool
    """

    use_sculpt_texture_paint: bool
    """ Use texture painting in Sculpt Mode

    :type: bool
    """

    use_sculpt_tools_tilt: bool
    """ Support for pen tablet tilt events in Sculpt Mode

    :type: bool
    """

    use_shader_node_previews: bool
    """ Enables previews in the shader node editor

    :type: bool
    """

    use_undo_legacy: bool
    """ Use legacy undo (slower than the new default one, but may be more stable in some cases)

    :type: bool
    """

    use_viewport_debug: bool
    """ Enable viewport debugging options for developers in the overlays pop-over

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
