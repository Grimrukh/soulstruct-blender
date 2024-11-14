import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .context import Context
from .ui_layout import UILayout

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Panel(bpy_struct):
    """Panel containing UI elements"""

    bl_category: str
    """ The category (tab) in which the panel will be displayed, when applicable

    :type: str
    """

    bl_context: str
    """ The context in which the panel belongs to. (TODO: explain the possible combinations bl_context/bl_region_type/bl_space_type)

    :type: str
    """

    bl_description: str
    """ The panel tooltip

    :type: str
    """

    bl_idname: str
    """ If this is set, the panel gets a custom ID, otherwise it takes the name of the class used to define the panel. For example, if the class name is "OBJECT_PT_hello", and bl_idname is not set by the script, then bl_idname = "OBJECT_PT_hello"

    :type: str
    """

    bl_label: str
    """ The panel label, shows up in the panel header at the right of the triangle used to collapse the panel

    :type: str
    """

    bl_options: set[str]
    """ Options for this panel type

    :type: set[str]
    """

    bl_order: int
    """ Panels with lower numbers are default ordered before panels with higher numbers

    :type: int
    """

    bl_owner_id: str
    """ The ID owning the data displayed in the panel, if any

    :type: str
    """

    bl_parent_id: str
    """ If this is set, the panel becomes a sub-panel

    :type: str
    """

    bl_region_type: str
    """ The region where the panel is going to be used in

    :type: str
    """

    bl_space_type: str
    """ The space where the panel is going to be used in

    :type: str
    """

    bl_translation_context: str | typing.Any
    """ Specific translation context, only define when the label needs to be disambiguated from others using the exact same label

    :type: str | typing.Any
    """

    bl_ui_units_x: int
    """ When set, defines popup panel width

    :type: int
    """

    custom_data: Constraint
    """ Panel data

    :type: Constraint
    """

    is_popover: bool
    """ 

    :type: bool
    """

    layout: UILayout
    """ Defines the structure of the panel in the UI

    :type: UILayout
    """

    text: str
    """ XXX todo

    :type: str
    """

    use_pin: bool
    """ Show the panel on all tabs

    :type: bool
    """

    is_registered: bool
    """ 

    :type: bool
    """

    @classmethod
    def poll(cls, context: Context) -> bool:
        """If this method returns a non-null output, then the panel can be drawn

        :param context:
        :type context: Context
        :return:
        :rtype: bool
        """
        ...

    def draw(self, context: Context):
        """Draw UI elements into the panel UI layout

        :param context:
        :type context: Context
        """
        ...

    def draw_header(self, context: Context):
        """Draw UI elements into the panel's header UI layout

        :param context:
        :type context: Context
        """
        ...

    def draw_header_preset(self, context: Context):
        """Draw UI elements for presets in the panel's header

        :param context:
        :type context: Context
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
