import typing
import collections.abc
import mathutils
from .scene import Scene
from .struct import Struct
from .bpy_struct import bpy_struct
from .id_override_library import IDOverrideLibrary
from .view_layer import ViewLayer
from .library import Library
from .anim_data import AnimData
from .image_preview import ImagePreview
from .library_weak_reference import LibraryWeakReference
from .asset_meta_data import AssetMetaData
from .depsgraph import Depsgraph

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ID(bpy_struct):
    """Base type for data-blocks, defining a unique name, linking from other libraries and garbage collection"""

    asset_data: AssetMetaData
    """ Additional data for an asset data-block

    :type: AssetMetaData
    """

    id_type: str
    """ Type identifier of this data-block

    :type: str
    """

    is_embedded_data: bool
    """ This data-block is not an independent one, but is actually a sub-data of another ID (typical example: root node trees or master collections)

    :type: bool
    """

    is_evaluated: bool
    """ Whether this ID is runtime-only, evaluated data-block, or actual data from .blend file

    :type: bool
    """

    is_library_indirect: bool
    """ Is this ID block linked indirectly

    :type: bool
    """

    is_missing: bool
    """ This data-block is a place-holder for missing linked data (i.e. it is [an override of] a linked data that could not be found anymore)

    :type: bool
    """

    is_runtime_data: bool
    """ This data-block is runtime data, i.e. it won't be saved in .blend file. Note that e.g. evaluated IDs are always runtime, so this value is only editable for data-blocks in Main data-base

    :type: bool
    """

    library: Library
    """ Library file the data-block is linked from

    :type: Library
    """

    library_weak_reference: LibraryWeakReference
    """ Weak reference to a data-block in another library .blend file (used to re-use already appended data instead of appending new copies)

    :type: LibraryWeakReference
    """

    name: str
    """ Unique data-block ID name (within a same type and library)

    :type: str
    """

    name_full: str
    """ Unique data-block ID name, including library one is any

    :type: str
    """

    original: ID
    """ Actual data-block from .blend file (Main database) that generated that evaluated one

    :type: ID
    """

    override_library: IDOverrideLibrary
    """ Library override data

    :type: IDOverrideLibrary
    """

    preview: ImagePreview
    """ Preview image and icon of this data-block (always None if not supported for this type of data)

    :type: ImagePreview
    """

    session_uid: int
    """ A session-wide unique identifier for the data block that remains the same across renames and internal reallocations. It does change when reloading the file

    :type: int
    """

    tag: bool
    """ Tools can use this to tag data for their own purposes (initial state is undefined)

    :type: bool
    """

    use_extra_user: bool
    """ Indicates whether an extra user is set or not (mainly for internal/debug usages)

    :type: bool
    """

    use_fake_user: bool
    """ Save this data-block even if it has no users

    :type: bool
    """

    users: int
    """ Number of times this data-block is referenced

    :type: int
    """

    def evaluated_get(self, depsgraph: Depsgraph) -> ID:
        """Get corresponding evaluated ID from the given dependency graph. Note that this does not ensure the dependency graph is fully evaluated, it just returns the result of the last evaluation

        :param depsgraph: Dependency graph to perform lookup in
        :type depsgraph: Depsgraph
        :return: New copy of the ID
        :rtype: ID
        """
        ...

    def copy(self) -> ID:
        """Create a copy of this data-block (not supported for all data-blocks). The result is added to the Blend-File Data (Main database), with all references to other data-blocks ensured to be from within the same Blend-File Data

        :return: New copy of the ID
        :rtype: ID
        """
        ...

    def asset_mark(self):
        """Enable easier reuse of the data-block through the Asset Browser, with the help of customizable metadata (like previews, descriptions and tags)"""
        ...

    def asset_clear(self):
        """Delete all asset metadata and turn the asset data-block back into a normal data-block"""
        ...

    def asset_generate_preview(self):
        """Generate preview image (might be scheduled in a background thread)"""
        ...

    def override_create(
        self, remap_local_usages: bool | typing.Any | None = False
    ) -> ID:
        """Create an overridden local copy of this linked data-block (not supported for all data-blocks)

        :param remap_local_usages: Whether local usages of the linked ID should be remapped to the new library override of it
        :type remap_local_usages: bool | typing.Any | None
        :return: New overridden local copy of the ID
        :rtype: ID
        """
        ...

    def override_hierarchy_create(
        self,
        scene: Scene,
        view_layer: ViewLayer,
        reference: ID | None = None,
        do_fully_editable: bool | typing.Any | None = False,
    ) -> ID:
        """Create an overridden local copy of this linked data-block, and most of its dependencies when it is a Collection or and Object

        :param scene: In which scene the new overrides should be instantiated
        :type scene: Scene
        :param view_layer: In which view layer the new overrides should be instantiated
        :type view_layer: ViewLayer
        :param reference: Another ID (usually an Object or Collection) used as a hint to decide where to instantiate the new overrides
        :type reference: ID | None
        :param do_fully_editable: Make all library overrides generated by this call fully editable by the user (none will be 'system overrides')
        :type do_fully_editable: bool | typing.Any | None
        :return: New overridden local copy of the root ID
        :rtype: ID
        """
        ...

    def user_clear(self):
        """Clear the user count of a data-block so its not saved, on reload the data will be removedThis function is for advanced use only, misuse can crash blender since the user
        count is used to prevent data being removed when it is used.

        """
        ...

    def user_remap(self, new_id: ID):
        """Replace all usage in the .blend file of this ID by new given one

        :param new_id: New ID to use
        :type new_id: ID
        """
        ...

    def make_local(
        self,
        clear_proxy: bool | typing.Any | None = True,
        clear_liboverride: bool | typing.Any | None = False,
    ) -> ID:
        """Make this datablock local, return local one (may be a copy of the original, in case it is also indirectly used)

        :param clear_proxy: Deprecated, has no effect
        :type clear_proxy: bool | typing.Any | None
        :param clear_liboverride: Remove potential library override data from the newly made local data
        :type clear_liboverride: bool | typing.Any | None
        :return: This ID, or the new ID if it was copied
        :rtype: ID
        """
        ...

    def user_of_id(self, id: ID) -> int:
        """Count the number of times that ID uses/references given one

        :param id: ID to count usages
        :type id: ID
        :return: Number of usages/references of given id by current data-block
        :rtype: int
        """
        ...

    def animation_data_create(self) -> AnimData:
        """Create animation data to this ID, note that not all ID types support this

        :return: New animation data or nullptr
        :rtype: AnimData
        """
        ...

    def animation_data_clear(self):
        """Clear animation on this ID"""
        ...

    def update_tag(self, refresh: set[str] | None = {}):
        """Tag the ID to update its display data, e.g. when calling `bpy.types.Scene.update`

        :param refresh: Type of updates to perform
        :type refresh: set[str] | None
        """
        ...

    def preview_ensure(self) -> ImagePreview:
        """Ensure that this ID has preview data (if ID type supports it)

        :return: The existing or created preview
        :rtype: ImagePreview
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
