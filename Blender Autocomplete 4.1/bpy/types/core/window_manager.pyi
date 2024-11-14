import typing
import collections.abc
import mathutils
from .operator_properties import OperatorProperties
from .key_map import KeyMap
from .struct import Struct
from .xr_session_state import XrSessionState
from .operator import Operator
from .asset_handle import AssetHandle
from .ui_popover import UIPopover
from .bpy_prop_collection import bpy_prop_collection
from .xr_session_settings import XrSessionSettings
from .window import Window
from .action import Action
from .bpy_struct import bpy_struct
from .ui_popup_menu import UIPopupMenu
from .timer import Timer
from .id import ID
from .key_configurations import KeyConfigurations
from .ui_pie_menu import UIPieMenu
from .event import Event

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WindowManager(ID, bpy_struct):
    """Window manager data-block defining open windows and other user interface data"""

    addon_filter: str
    """ Filter add-ons by category

    :type: str
    """

    addon_search: str
    """ Filter by add-on name, author & category

    :type: str
    """

    addon_support: set[str]
    """ Display support level

    :type: set[str]
    """

    asset_path_dummy: str
    """ Full path to the Blender file containing the active asset

    :type: str
    """

    is_interface_locked: bool
    """ If true, the interface is currently locked by a running job and data shouldn't be modified from application timers. Otherwise, the running job might conflict with the handler causing unexpected results or even crashes

    :type: bool
    """

    keyconfigs: KeyConfigurations
    """ Registered key configurations

    :type: KeyConfigurations
    """

    operators: bpy_prop_collection[Operator]
    """ Operator registry

    :type: bpy_prop_collection[Operator]
    """

    pose_assets: bpy_prop_collection[AssetHandle]
    """ 

    :type: bpy_prop_collection[AssetHandle]
    """

    poselib_previous_action: Action
    """ 

    :type: Action
    """

    preset_name: str | typing.Any
    """ Name for new preset

    :type: str | typing.Any
    """

    windows: bpy_prop_collection[Window]
    """ Open windows

    :type: bpy_prop_collection[Window]
    """

    xr_session_settings: XrSessionSettings
    """ 

    :type: XrSessionSettings
    """

    xr_session_state: XrSessionState
    """ Runtime state information about the VR session

    :type: XrSessionState
    """

    clipboard: str
    """ Clipboard text storage.

    :type: str
    """

    @classmethod
    def fileselect_add(cls, operator: Operator | None):
        """Opens a file selector with an operator. The string properties 'filepath', 'filename', 'directory' and a 'files' collection are assigned when present in the operator

        :param operator: Operator to call
        :type operator: Operator | None
        """
        ...

    @classmethod
    def modal_handler_add(cls, operator: Operator | None) -> bool:
        """Add a modal handler to the window manager, for the given modal operator (called by invoke() with self, just before returning {'RUNNING_MODAL'})

        :param operator: Operator to call
        :type operator: Operator | None
        :return: Whether adding the handler was successful
        :rtype: bool
        """
        ...

    def event_timer_add(
        self, time_step: float | None, window: Window | None = None
    ) -> Timer:
        """Add a timer to the given window, to generate periodic 'TIMER' events

        :param time_step: Time Step, Interval in seconds between timer events
        :type time_step: float | None
        :param window: Window to attach the timer to, or None
        :type window: Window | None
        :return:
        :rtype: Timer
        """
        ...

    def event_timer_remove(self, timer: Timer):
        """event_timer_remove

        :param timer:
        :type timer: Timer
        """
        ...

    @classmethod
    def gizmo_group_type_ensure(cls, identifier: str | typing.Any):
        """Activate an existing widget group (when the persistent option isn't set)

        :param identifier: Gizmo group type name
        :type identifier: str | typing.Any
        """
        ...

    @classmethod
    def gizmo_group_type_unlink_delayed(cls, identifier: str | typing.Any):
        """Unlink a widget group (when the persistent option is set)

        :param identifier: Gizmo group type name
        :type identifier: str | typing.Any
        """
        ...

    def progress_begin(self, min: float | None, max: float | None):
        """Start progress report

        :param min: min, any value in range [0,9999]
        :type min: float | None
        :param max: max, any value in range [min+1,9998]
        :type max: float | None
        """
        ...

    def progress_update(self, value: float | None):
        """Update the progress feedback

        :param value: value, Any value between min and max as set in progress_begin()
        :type value: float | None
        """
        ...

    def progress_end(self):
        """Terminate progress report"""
        ...

    @classmethod
    def invoke_props_popup(cls, operator: Operator | None, event: Event | None):
        """Operator popup invoke (show operator properties and execute it automatically on changes)

        :param operator: Operator to call
        :type operator: Operator | None
        :param event: Event
        :type event: Event | None
        :return: result
        """
        ...

    @classmethod
    def invoke_props_dialog(
        cls,
        operator: Operator | None,
        width: typing.Any | None = 300,
        title: str | typing.Any = "",
        confirm_text: str | typing.Any = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
    ):
        """Operator dialog (non-autoexec popup) invoke (show operator properties and only execute it on click on OK button)

        :param operator: Operator to call
        :type operator: Operator | None
        :param width: Width of the popup
        :type width: typing.Any | None
        :param title: Title, Optional text to show as title of the popup
        :type title: str | typing.Any
        :param confirm_text: Confirm Text, Optional text to show instead to the default "OK" confirmation button text
        :type confirm_text: str | typing.Any
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :return: result
        """
        ...

    @classmethod
    def invoke_search_popup(cls, operator: Operator | None):
        """Operator search popup invoke which searches values of the operator's `bpy.types.Operator.bl_property` (which must be an EnumProperty), executing it on confirmation

        :param operator: Operator to call
        :type operator: Operator | None
        """
        ...

    @classmethod
    def invoke_popup(cls, operator: Operator | None, width: typing.Any | None = 300):
        """Operator popup invoke (only shows operator's properties, without executing it)

        :param operator: Operator to call
        :type operator: Operator | None
        :param width: Width of the popup
        :type width: typing.Any | None
        :return: result
        """
        ...

    @classmethod
    def invoke_confirm(
        cls,
        operator: Operator | None,
        event: Event | None,
        title: str | typing.Any = "",
        message: str | typing.Any = "",
        confirm_text: str | typing.Any = "",
        icon: str | None = "WARNING",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
    ):
        """Operator confirmation popup (only to let user confirm the execution, no operator properties shown)

        :param operator: Operator to call
        :type operator: Operator | None
        :param event: Event
        :type event: Event | None
        :param title: Title, Optional text to show as title of the popup
        :type title: str | typing.Any
        :param message: Message, Optional first line of content text
        :type message: str | typing.Any
        :param confirm_text: Confirm Text, Optional text to show instead to the default "OK" confirmation button text
        :type confirm_text: str | typing.Any
        :param icon: Icon, Optional icon displayed in the dialog
        :type icon: str | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :return: result
        """
        ...

    @classmethod
    def popmenu_begin__internal(
        cls, title: str | typing.Any, icon: str | None = "NONE"
    ) -> UIPopupMenu:
        """popmenu_begin__internal

        :param title:
        :type title: str | typing.Any
        :param icon: icon
        :type icon: str | None
        :return:
        :rtype: UIPopupMenu
        """
        ...

    @classmethod
    def popmenu_end__internal(cls, menu: UIPopupMenu):
        """popmenu_end__internal

        :param menu:
        :type menu: UIPopupMenu
        """
        ...

    @classmethod
    def popover_begin__internal(
        cls,
        ui_units_x: typing.Any | None = 0,
        from_active_button: bool | typing.Any | None = False,
    ) -> UIPopover:
        """popover_begin__internal

        :param ui_units_x: ui_units_x
        :type ui_units_x: typing.Any | None
        :param from_active_button: Use Button, Use the active button for positioning
        :type from_active_button: bool | typing.Any | None
        :return:
        :rtype: UIPopover
        """
        ...

    @classmethod
    def popover_end__internal(cls, menu: UIPopover, keymap: KeyMap | None = None):
        """popover_end__internal

        :param menu:
        :type menu: UIPopover
        :param keymap: Key Map, Active key map
        :type keymap: KeyMap | None
        """
        ...

    @classmethod
    def piemenu_begin__internal(
        cls, title: str | typing.Any, icon: str | None = "NONE", event: Event = None
    ) -> UIPieMenu:
        """piemenu_begin__internal

        :param title:
        :type title: str | typing.Any
        :param icon: icon
        :type icon: str | None
        :param event:
        :type event: Event
        :return:
        :rtype: UIPieMenu
        """
        ...

    @classmethod
    def piemenu_end__internal(cls, menu: UIPieMenu):
        """piemenu_end__internal

        :param menu:
        :type menu: UIPieMenu
        """
        ...

    @classmethod
    def operator_properties_last(cls, operator: str | typing.Any) -> OperatorProperties:
        """operator_properties_last

        :param operator:
        :type operator: str | typing.Any
        :return:
        :rtype: OperatorProperties
        """
        ...

    def print_undo_steps(self):
        """print_undo_steps"""
        ...

    @classmethod
    def tag_script_reload(cls):
        """Tag for refreshing the interface after scripts have been reloaded"""
        ...

    def popover(
        self, draw_func, *, ui_units_x=0, keymap=None, from_active_button=False
    ):
        """

        :param draw_func:
        :param ui_units_x:
        :param keymap:
        :param from_active_button:
        """
        ...

    def popup_menu(self, draw_func, *, title="", icon="NONE"):
        """Popup menus can be useful for creating menus without having to register menu classes.Note that they will not block the scripts execution, so the caller can't wait for user input.

        :param draw_func:
        :param title:
        :param icon:
        """
        ...

    def popup_menu_pie(self, event, draw_func, *, title="", icon="NONE"):
        """

        :param event:
        :param draw_func:
        :param title:
        :param icon:
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

    @classmethod
    def draw_cursor_add(
        cls,
        callback: typing.Any | None,
        args: tuple | None,
        space_type: str | None,
        region_type: str | None,
    ) -> typing.Any:
        """Add a new draw cursor handler to this space type.
        It will be called every time the cursor for the specified region in the space type will be drawn.
        Note: All arguments are positional only for now.

                :param callback: A function that will be called when the cursor is drawn.
        It gets the specified arguments as input with the mouse position (tuple) as last argument.
                :type callback: typing.Any | None
                :param args: Arguments that will be passed to the callback.
                :type args: tuple | None
                :param space_type: The space type the callback draws in; for example VIEW_3D. (`bpy.types.Space.type`)
                :type space_type: str | None
                :param region_type: The region type the callback draws in; usually WINDOW. (`bpy.types.Region.type`)
                :type region_type: str | None
                :return: Handler that can be removed later on.
                :rtype: typing.Any
        """
        ...

    @classmethod
    def draw_cursor_remove(cls, handler: typing.Any | None):
        """Remove a draw cursor handler that was added previously.

        :param handler: The draw cursor handler that should be removed.
        :type handler: typing.Any | None
        """
        ...
