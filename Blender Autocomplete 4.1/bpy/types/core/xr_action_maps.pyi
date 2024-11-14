import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .xr_action_map import XrActionMap
from .bpy_struct import bpy_struct
from .xr_session_state import XrSessionState

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class XrActionMaps(bpy_prop_collection[XrActionMap], bpy_struct):
    """Collection of XR action maps"""

    @classmethod
    def new(
        cls,
        xr_session_state: XrSessionState,
        name: str | typing.Any,
        replace_existing: bool | None,
    ) -> XrActionMap:
        """new

        :param xr_session_state: XR Session State
        :type xr_session_state: XrSessionState
        :param name: Name
        :type name: str | typing.Any
        :param replace_existing: Replace Existing, Replace any existing actionmap with the same name
        :type replace_existing: bool | None
        :return: Action Map, Added action map
        :rtype: XrActionMap
        """
        ...

    @classmethod
    def new_from_actionmap(
        cls, xr_session_state: XrSessionState, actionmap: XrActionMap
    ) -> XrActionMap:
        """new_from_actionmap

        :param xr_session_state: XR Session State
        :type xr_session_state: XrSessionState
        :param actionmap: Action Map, Action map to use as a reference
        :type actionmap: XrActionMap
        :return: Action Map, Added action map
        :rtype: XrActionMap
        """
        ...

    @classmethod
    def remove(cls, xr_session_state: XrSessionState, actionmap: XrActionMap):
        """remove

        :param xr_session_state: XR Session State
        :type xr_session_state: XrSessionState
        :param actionmap: Action Map, Removed action map
        :type actionmap: XrActionMap
        """
        ...

    @classmethod
    def find(
        cls, xr_session_state: XrSessionState, name: str | typing.Any
    ) -> XrActionMap:
        """find

        :param xr_session_state: XR Session State
        :type xr_session_state: XrSessionState
        :param name: Name
        :type name: str | typing.Any
        :return: Action Map, The action map with the given name
        :rtype: XrActionMap
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
