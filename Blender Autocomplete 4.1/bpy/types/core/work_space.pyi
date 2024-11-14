import typing
import collections.abc
import mathutils
from .screen import Screen
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .wm_owner_i_ds import wmOwnerIDs
from .bpy_struct import bpy_struct
from .wm_tools import wmTools
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WorkSpace(ID, bpy_struct):
    """Workspace data-block, defining the working environment for the user"""

    active_addon: int | None
    """ Active Add-on in the Workspace Add-ons filter

    :type: int | None
    """

    active_pose_asset_index: int | None
    """ Per workspace index of the active pose asset

    :type: int | None
    """

    asset_library_reference: str
    """ Active asset library to show in the UI, not used by the Asset Browser (which has its own active asset library)

    :type: str
    """

    object_mode: str
    """ Switch to this object mode when activating the workspace

    :type: str
    """

    owner_ids: wmOwnerIDs
    """ 

    :type: wmOwnerIDs
    """

    screens: bpy_prop_collection[Screen]
    """ Screen layouts of a workspace

    :type: bpy_prop_collection[Screen]
    """

    tools: wmTools
    """ 

    :type: wmTools
    """

    use_filter_by_owner: bool
    """ Filter the UI by tags

    :type: bool
    """

    use_pin_scene: bool
    """ Remember the last used scene for the workspace and switch to it whenever this workspace is activated again

    :type: bool
    """

    @classmethod
    def status_text_set_internal(cls, text: str | None):
        """Set the status bar text, typically key shortcuts for modal operators

        :param text: Text, New string for the status bar, None clears the text
        :type text: str | None
        """
        ...

    def status_text_set(self, text):
        """Set the status text or None to clear,
        When text is a function, this will be called with the (header, context) arguments.

                :param text:
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
