import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .id_override_library_properties import IDOverrideLibraryProperties
from .id import ID
from .view_layer import ViewLayer
from .scene import Scene

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class IDOverrideLibrary(bpy_struct):
    """Struct gathering all data needed by overridden linked IDs"""

    hierarchy_root: ID
    """ Library override ID used as root of the override hierarchy this ID is a member of

    :type: ID
    """

    is_in_hierarchy: bool
    """ Whether this library override is defined as part of a library hierarchy, or as a single, isolated and autonomous override

    :type: bool
    """

    is_system_override: bool
    """ Whether this library override exists only for the override hierarchy, or if it is actually editable by the user

    :type: bool
    """

    properties: IDOverrideLibraryProperties
    """ List of overridden properties

    :type: IDOverrideLibraryProperties
    """

    reference: ID
    """ Linked ID used as reference by this override

    :type: ID
    """

    def operations_update(self):
        """Update the library override operations based on the differences between this override ID and its reference"""
        ...

    def reset(
        self,
        do_hierarchy: bool | typing.Any | None = True,
        set_system_override: bool | typing.Any | None = False,
    ):
        """Reset this override to match again its linked reference ID

        :param do_hierarchy: Also reset all the dependencies of this override to match their reference linked IDs
        :type do_hierarchy: bool | typing.Any | None
        :param set_system_override: Reset all user-editable overrides as (non-editable) system overrides
        :type set_system_override: bool | typing.Any | None
        """
        ...

    def destroy(self, do_hierarchy: bool | typing.Any | None = True):
        """Delete this override ID and remap its usages to its linked reference ID instead

        :param do_hierarchy: Also delete all the dependencies of this override and remap their usages to their reference linked IDs
        :type do_hierarchy: bool | typing.Any | None
        """
        ...

    def resync(
        self,
        scene: Scene,
        view_layer: ViewLayer | None = None,
        residual_storage: Collection | None = None,
        do_hierarchy_enforce: bool | typing.Any | None = False,
        do_whole_hierarchy: bool | typing.Any | None = False,
    ) -> bool:
        """Resync the data-block and its sub-hierarchy, or the whole hierarchy if requested

        :param scene: The scene to operate in (for contextual things like keeping active object active, ensuring all overridden objects remain instantiated, etc.)
        :type scene: Scene
        :param view_layer: The view layer to operate in (same usage as the scene data, in case it is not provided the scene's collection will be used instead)
        :type view_layer: ViewLayer | None
        :param residual_storage: Collection where to store objects that are instantiated in any other collection anymore (garbage collection, will be created if needed and none is provided)
        :type residual_storage: Collection | None
        :param do_hierarchy_enforce: Enforce restoring the dependency hierarchy between data-blocks to match the one from the reference linked hierarchy (WARNING: if some ID pointers have been purposedly overridden, these will be reset to their default value)
        :type do_hierarchy_enforce: bool | typing.Any | None
        :param do_whole_hierarchy: Resync the whole hierarchy this data-block belongs to, not only its own sub-hierarchy
        :type do_whole_hierarchy: bool | typing.Any | None
        :return: Success, Whether the resync process was successful or not
        :rtype: bool
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
