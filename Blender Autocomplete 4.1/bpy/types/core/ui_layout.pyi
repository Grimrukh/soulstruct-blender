import typing
import collections.abc
import mathutils
from .operator_properties import OperatorProperties
from .movie_tracking_track import MovieTrackingTrack
from .image_user import ImageUser
from .node_tree import NodeTree
from .struct import Struct
from .stereo3d_format import Stereo3dFormat
from .file_select_params import FileSelectParams
from .texture_slot import TextureSlot
from .key_map_item import KeyMapItem
from .node_tree_interface import NodeTreeInterface
from .image_format_settings import ImageFormatSettings
from .image import Image
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .node_socket import NodeSocket
from .node import Node
from .id import ID
from .movie_clip_user import MovieClipUser

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UILayout(bpy_struct):
    """User interface layout in a panel or header"""

    activate_init: bool
    """ When true, buttons defined in popups will be activated on first display (use so you can type into a field without having to click on it first)

    :type: bool
    """

    active: bool | None
    """ 

    :type: bool | None
    """

    active_default: bool | None
    """ When true, an operator button defined after this will be activated when pressing return(use with popup dialogs)

    :type: bool | None
    """

    alert: bool
    """ 

    :type: bool
    """

    alignment: str
    """ 

    :type: str
    """

    direction: str
    """ 

    :type: str
    """

    emboss: str
    """ 

    :type: str
    """

    enabled: bool
    """ When false, this (sub)layout is grayed out

    :type: bool
    """

    operator_context: str
    """ 

    :type: str
    """

    scale_x: float
    """ Scale factor along the X for items in this (sub)layout

    :type: float
    """

    scale_y: float
    """ Scale factor along the Y for items in this (sub)layout

    :type: float
    """

    ui_units_x: float
    """ Fixed size along the X for items in this (sub)layout

    :type: float
    """

    ui_units_y: float
    """ Fixed size along the Y for items in this (sub)layout

    :type: float
    """

    use_property_decorate: bool
    """ 

    :type: bool
    """

    use_property_split: bool
    """ 

    :type: bool
    """

    def row(
        self,
        align: bool | typing.Any | None = False,
        heading: str | typing.Any = "",
        heading_ctxt: str | typing.Any = "",
        translate: bool | typing.Any | None = True,
    ) -> UILayout:
        """Sub-layout. Items placed in this sublayout are placed next to each other in a row

        :param align: Align buttons to each other
        :type align: bool | typing.Any | None
        :param heading: Heading, Label to insert into the layout for this sub-layout
        :type heading: str | typing.Any
        :param heading_ctxt: Override automatic translation context of the given heading
        :type heading_ctxt: str | typing.Any
        :param translate: Translate the given heading, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :return: Sub-layout to put items in
        :rtype: UILayout
        """
        ...

    def column(
        self,
        align: bool | typing.Any | None = False,
        heading: str | typing.Any = "",
        heading_ctxt: str | typing.Any = "",
        translate: bool | typing.Any | None = True,
    ) -> UILayout:
        """Sub-layout. Items placed in this sublayout are placed under each other in a column

        :param align: Align buttons to each other
        :type align: bool | typing.Any | None
        :param heading: Heading, Label to insert into the layout for this sub-layout
        :type heading: str | typing.Any
        :param heading_ctxt: Override automatic translation context of the given heading
        :type heading_ctxt: str | typing.Any
        :param translate: Translate the given heading, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :return: Sub-layout to put items in
        :rtype: UILayout
        """
        ...

    def panel(
        self, idname: str | typing.Any, default_closed: bool | typing.Any | None = False
    ):
        """Creates a collapsable panel. Whether it is open or closed is stored in the region using the given idname. This can only be used when the panel has the full width of the panel region available to it. So it can't be used in e.g. in a box or columns

                :param idname: Identifier of the panel
                :type idname: str | typing.Any
                :param default_closed: Open by Default, When true, the panel will be open the first time it is shown
                :type default_closed: bool | typing.Any | None
                :return: layout_header, Sub-layout to put items in, `UILayout`

        layout_body, Sub-layout to put items in. Will be none if the panel is collapsed, `UILayout`
        """
        ...

    def panel_prop(self, data: typing.Any, property: str | typing.Any):
        """Similar to .panel(...) but instead of storing whether it is open or closed in the region, it is stored in the provided boolean property. This should be used when multiple instances of the same panel can exist. For example one for every item in a collection property or list. This can only be used when the panel has the full width of the panel region available to it. So it can't be used in e.g. in a box or columns

                :param data: Data from which to take the open-state property
                :type data: typing.Any
                :param property: Identifier of the boolean property that determines whether the panel is open or closed
                :type property: str | typing.Any
                :return: layout_header, Sub-layout to put items in, `UILayout`

        layout_body, Sub-layout to put items in. Will be none if the panel is collapsed, `UILayout`
        """
        ...

    def column_flow(
        self, columns: typing.Any | None = 0, align: bool | typing.Any | None = False
    ) -> UILayout:
        """column_flow

        :param columns: Number of columns, 0 is automatic
        :type columns: typing.Any | None
        :param align: Align buttons to each other
        :type align: bool | typing.Any | None
        :return: Sub-layout to put items in
        :rtype: UILayout
        """
        ...

    def grid_flow(
        self,
        row_major: bool | typing.Any | None = False,
        columns: typing.Any | None = 0,
        even_columns: bool | typing.Any | None = False,
        even_rows: bool | typing.Any | None = False,
        align: bool | typing.Any | None = False,
    ) -> UILayout:
        """grid_flow

        :param row_major: Fill row by row, instead of column by column
        :type row_major: bool | typing.Any | None
        :param columns: Number of columns, positive are absolute fixed numbers, 0 is automatic, negative are automatic multiple numbers along major axis (e.g. -2 will only produce 2, 4, 6 etc. columns for row major layout, and 2, 4, 6 etc. rows for column major layout)
        :type columns: typing.Any | None
        :param even_columns: All columns will have the same width
        :type even_columns: bool | typing.Any | None
        :param even_rows: All rows will have the same height
        :type even_rows: bool | typing.Any | None
        :param align: Align buttons to each other
        :type align: bool | typing.Any | None
        :return: Sub-layout to put items in
        :rtype: UILayout
        """
        ...

    def box(self) -> UILayout:
        """Sublayout (items placed in this sublayout are placed under each other in a column and are surrounded by a box)

        :return: Sub-layout to put items in
        :rtype: UILayout
        """
        ...

    def split(
        self, factor: typing.Any | None = 0.0, align: bool | typing.Any | None = False
    ) -> UILayout:
        """split

        :param factor: Percentage, Percentage of width to split at (leave unset for automatic calculation)
        :type factor: typing.Any | None
        :param align: Align buttons to each other
        :type align: bool | typing.Any | None
        :return: Sub-layout to put items in
        :rtype: UILayout
        """
        ...

    def menu_pie(self) -> UILayout:
        """Sublayout. Items placed in this sublayout are placed in a radial fashion around the menu center)

        :return: Sub-layout to put items in
        :rtype: UILayout
        """
        ...

    @classmethod
    def icon(cls, data: typing.Any) -> int:
        """Return the custom icon for this data, use it e.g. to get materials or texture icons

        :param data: Data from which to take the icon
        :type data: typing.Any
        :return: Icon identifier
        :rtype: int
        """
        ...

    @classmethod
    def enum_item_name(
        cls, data: typing.Any, property: str | typing.Any, identifier: str | typing.Any
    ) -> str | typing.Any:
        """Return the UI name for this enum item

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param identifier: Identifier of the enum item
        :type identifier: str | typing.Any
        :return: UI name of the enum item
        :rtype: str | typing.Any
        """
        ...

    @classmethod
    def enum_item_description(
        cls, data: typing.Any, property: str | typing.Any, identifier: str | typing.Any
    ) -> str | typing.Any:
        """Return the UI description for this enum item

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param identifier: Identifier of the enum item
        :type identifier: str | typing.Any
        :return: UI description of the enum item
        :rtype: str | typing.Any
        """
        ...

    @classmethod
    def enum_item_icon(
        cls, data: typing.Any, property: str | typing.Any, identifier: str | typing.Any
    ) -> int:
        """Return the icon for this enum item

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param identifier: Identifier of the enum item
        :type identifier: str | typing.Any
        :return: Icon identifier
        :rtype: int
        """
        ...

    def prop(
        self,
        data: typing.Any,
        property: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        placeholder: str | typing.Any = "",
        expand: bool | typing.Any | None = False,
        slider: bool | typing.Any | None = False,
        toggle: typing.Any | None = -1,
        icon_only: bool | typing.Any | None = False,
        event: bool | typing.Any | None = False,
        full_event: bool | typing.Any | None = False,
        emboss: bool | typing.Any | None = True,
        index: typing.Any | None = -1,
        icon_value: typing.Any | None = 0,
        invert_checkbox: bool | typing.Any | None = False,
    ):
        """Item. Exposes an RNA item and places it into the layout

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param placeholder: Hint describing the expected value when empty
        :type placeholder: str | typing.Any
        :param expand: Expand button to show more detail
        :type expand: bool | typing.Any | None
        :param slider: Use slider widget for numeric values
        :type slider: bool | typing.Any | None
        :param toggle: Use toggle widget for boolean values, or a checkbox when disabled (the default is -1 which uses toggle only when an icon is displayed)
        :type toggle: typing.Any | None
        :param icon_only: Draw only icons in buttons, no text
        :type icon_only: bool | typing.Any | None
        :param event: Use button to input key events
        :type event: bool | typing.Any | None
        :param full_event: Use button to input full events including modifiers
        :type full_event: bool | typing.Any | None
        :param emboss: Draw the button itself, not just the icon/text. When false, corresponds to the 'NONE_OR_STATUS' layout emboss type
        :type emboss: bool | typing.Any | None
        :param index: The index of this button, when set a single member of an array can be accessed, when set to -1 all array members are used
        :type index: typing.Any | None
        :param icon_value: Icon Value, Override automatic icon of the item
        :type icon_value: typing.Any | None
        :param invert_checkbox: Draw checkbox value inverted
        :type invert_checkbox: bool | typing.Any | None
        """
        ...

    def props_enum(self, data: typing.Any, property: str | typing.Any):
        """props_enum

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def prop_menu_enum(
        self,
        data: typing.Any,
        property: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
    ):
        """prop_menu_enum

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        """
        ...

    def prop_with_popover(
        self,
        data: typing.Any,
        property: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        icon_only: bool | typing.Any | None = False,
        panel: str | typing.Any = None,
    ):
        """prop_with_popover

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param icon_only: Draw only icons in tabs, no text
        :type icon_only: bool | typing.Any | None
        :param panel: Identifier of the panel
        :type panel: str | typing.Any
        """
        ...

    def prop_with_menu(
        self,
        data: typing.Any,
        property: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        icon_only: bool | typing.Any | None = False,
        menu: str | typing.Any = None,
    ):
        """prop_with_menu

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param icon_only: Draw only icons in tabs, no text
        :type icon_only: bool | typing.Any | None
        :param menu: Identifier of the menu
        :type menu: str | typing.Any
        """
        ...

    def prop_tabs_enum(
        self,
        data: typing.Any,
        property: str | typing.Any,
        data_highlight: typing.Any = None,
        property_highlight: str | typing.Any = "",
        icon_only: bool | typing.Any | None = False,
    ):
        """prop_tabs_enum

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param data_highlight: Data from which to take highlight property
        :type data_highlight: typing.Any
        :param property_highlight: Identifier of highlight property in data
        :type property_highlight: str | typing.Any
        :param icon_only: Draw only icons in tabs, no text
        :type icon_only: bool | typing.Any | None
        """
        ...

    def prop_enum(
        self,
        data: typing.Any,
        property: str | typing.Any,
        value: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
    ):
        """prop_enum

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param value: Enum property value
        :type value: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        """
        ...

    def prop_search(
        self,
        data: typing.Any,
        property: str | typing.Any,
        search_data: typing.Any,
        search_property: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        results_are_suggestions: bool | typing.Any | None = False,
    ):
        """prop_search

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param search_data: Data from which to take collection to search in
        :type search_data: typing.Any
        :param search_property: Identifier of search collection property
        :type search_property: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param results_are_suggestions: Accept inputs that do not match any item
        :type results_are_suggestions: bool | typing.Any | None
        """
        ...

    def prop_decorator(
        self,
        data: typing.Any,
        property: str | typing.Any,
        index: typing.Any | None = -1,
    ):
        """prop_decorator

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param index: The index of this button, when set a single member of an array can be accessed, when set to -1 all array members are used
        :type index: typing.Any | None
        """
        ...

    def operator(
        self,
        operator: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        emboss: bool | typing.Any | None = True,
        depress: bool | typing.Any | None = False,
        icon_value: typing.Any | None = 0,
    ) -> OperatorProperties:
        """Item. Places a button into the layout to call an Operator

        :param operator: Identifier of the operator
        :type operator: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param emboss: Draw the button itself, not just the icon/text
        :type emboss: bool | typing.Any | None
        :param depress: Draw pressed in
        :type depress: bool | typing.Any | None
        :param icon_value: Icon Value, Override automatic icon of the item
        :type icon_value: typing.Any | None
        :return: Operator properties to fill in
        :rtype: OperatorProperties
        """
        ...

    def operator_menu_hold(
        self,
        operator: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        emboss: bool | typing.Any | None = True,
        depress: bool | typing.Any | None = False,
        icon_value: typing.Any | None = 0,
        menu: str | typing.Any = None,
    ) -> OperatorProperties:
        """Item. Places a button into the layout to call an Operator

        :param operator: Identifier of the operator
        :type operator: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param emboss: Draw the button itself, not just the icon/text
        :type emboss: bool | typing.Any | None
        :param depress: Draw pressed in
        :type depress: bool | typing.Any | None
        :param icon_value: Icon Value, Override automatic icon of the item
        :type icon_value: typing.Any | None
        :param menu: Identifier of the menu
        :type menu: str | typing.Any
        :return: Operator properties to fill in
        :rtype: OperatorProperties
        """
        ...

    def operator_enum(
        self,
        operator: str | typing.Any,
        property: str | typing.Any,
        icon_only: bool | typing.Any | None = False,
    ):
        """operator_enum

        :param operator: Identifier of the operator
        :type operator: str | typing.Any
        :param property: Identifier of property in operator
        :type property: str | typing.Any
        :param icon_only: Draw only icons in buttons, no text
        :type icon_only: bool | typing.Any | None
        """
        ...

    def operator_menu_enum(
        self,
        operator: str | typing.Any,
        property: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
    ) -> OperatorProperties:
        """operator_menu_enum

        :param operator: Identifier of the operator
        :type operator: str | typing.Any
        :param property: Identifier of property in operator
        :type property: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :return: Operator properties to fill in
        :rtype: OperatorProperties
        """
        ...

    def label(
        self,
        *,  # must use keywords
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        icon_value: typing.Any | None = 0,
    ):
        """Item. Displays text and/or icon in the layout

        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param icon_value: Icon Value, Override automatic icon of the item
        :type icon_value: typing.Any | None
        """
        ...

    def menu(
        self,
        menu: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        icon_value: typing.Any | None = 0,
    ):
        """menu

        :param menu: Identifier of the menu
        :type menu: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param icon_value: Icon Value, Override automatic icon of the item
        :type icon_value: typing.Any | None
        """
        ...

    def menu_contents(self, menu: str | typing.Any):
        """menu_contents

        :param menu: Identifier of the menu
        :type menu: str | typing.Any
        """
        ...

    def popover(
        self,
        panel: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        icon: str | None = "NONE",
        icon_value: typing.Any | None = 0,
    ):
        """popover

        :param panel: Identifier of the panel
        :type panel: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param icon: Icon, Override automatic icon of the item
        :type icon: str | None
        :param icon_value: Icon Value, Override automatic icon of the item
        :type icon_value: typing.Any | None
        """
        ...

    def popover_group(
        self,
        space_type: str | None,
        region_type: str | None,
        context: str | typing.Any,
        category: str | typing.Any,
    ):
        """popover_group

        :param space_type: Space Type
        :type space_type: str | None
        :param region_type: Region Type
        :type region_type: str | None
        :param context: panel type context
        :type context: str | typing.Any
        :param category: panel type category
        :type category: str | typing.Any
        """
        ...

    def separator(self, factor: typing.Any | None = 1.0):
        """Item. Inserts empty space into the layout between items

        :param factor: Percentage, Percentage of width to space (leave unset for default space)
        :type factor: typing.Any | None
        """
        ...

    def separator_spacer(self):
        """Item. Inserts horizontal spacing empty space into the layout between items"""
        ...

    def progress(
        self,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
        factor: typing.Any | None = 0.0,
        type: str | None = "BAR",
    ):
        """Progress indicator

        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        :param factor: Factor, Amount of progress from 0.0f to 1.0f
        :type factor: typing.Any | None
        :param type: Type, The type of progress indicator
        :type type: str | None
        """
        ...

    def context_pointer_set(self, name: str | typing.Any, data: typing.Any | None):
        """context_pointer_set

        :param name: Name, Name of entry in the context
        :type name: str | typing.Any
        :param data: Pointer to put in context
        :type data: typing.Any | None
        """
        ...

    def template_header(self):
        """Inserts common Space header UI (editor type selector)"""
        ...

    def template_ID(
        self,
        data: typing.Any,
        property: str | typing.Any,
        new: str | typing.Any = "",
        open: str | typing.Any = "",
        unlink: str | typing.Any = "",
        filter: str | None = "ALL",
        live_icon: bool | typing.Any | None = False,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
    ):
        """template_ID

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param new: Operator identifier to create a new ID block
        :type new: str | typing.Any
        :param open: Operator identifier to open a file for creating a new ID block
        :type open: str | typing.Any
        :param unlink: Operator identifier to unlink the ID block
        :type unlink: str | typing.Any
        :param filter: Optionally limit the items which can be selected
        :type filter: str | None
        :param live_icon: Show preview instead of fixed icon
        :type live_icon: bool | typing.Any | None
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        """
        ...

    def template_ID_preview(
        self,
        data: typing.Any,
        property: str | typing.Any,
        new: str | typing.Any = "",
        open: str | typing.Any = "",
        unlink: str | typing.Any = "",
        rows: typing.Any | None = 0,
        cols: typing.Any | None = 0,
        filter: str | None = "ALL",
        hide_buttons: bool | typing.Any | None = False,
    ):
        """template_ID_preview

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param new: Operator identifier to create a new ID block
        :type new: str | typing.Any
        :param open: Operator identifier to open a file for creating a new ID block
        :type open: str | typing.Any
        :param unlink: Operator identifier to unlink the ID block
        :type unlink: str | typing.Any
        :param rows: Number of thumbnail preview rows to display
        :type rows: typing.Any | None
        :param cols: Number of thumbnail preview columns to display
        :type cols: typing.Any | None
        :param filter: Optionally limit the items which can be selected
        :type filter: str | None
        :param hide_buttons: Show only list, no buttons
        :type hide_buttons: bool | typing.Any | None
        """
        ...

    def template_any_ID(
        self,
        data: typing.Any,
        property: str | typing.Any,
        type_property: str | typing.Any,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
    ):
        """template_any_ID

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param type_property: Identifier of property in data giving the type of the ID-blocks to use
        :type type_property: str | typing.Any
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        """
        ...

    def template_ID_tabs(
        self,
        data: typing.Any,
        property: str | typing.Any,
        new: str | typing.Any = "",
        menu: str | typing.Any = "",
        filter: str | None = "ALL",
    ):
        """template_ID_tabs

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param new: Operator identifier to create a new ID block
        :type new: str | typing.Any
        :param menu: Context menu identifier
        :type menu: str | typing.Any
        :param filter: Optionally limit the items which can be selected
        :type filter: str | None
        """
        ...

    def template_search(
        self,
        data: typing.Any,
        property: str | typing.Any,
        search_data: typing.Any,
        search_property: str | typing.Any,
        new: str | typing.Any = "",
        unlink: str | typing.Any = "",
    ):
        """template_search

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param search_data: Data from which to take collection to search in
        :type search_data: typing.Any
        :param search_property: Identifier of search collection property
        :type search_property: str | typing.Any
        :param new: Operator identifier to create a new item for the collection
        :type new: str | typing.Any
        :param unlink: Operator identifier to unlink or delete the active item from the collection
        :type unlink: str | typing.Any
        """
        ...

    def template_search_preview(
        self,
        data: typing.Any,
        property: str | typing.Any,
        search_data: typing.Any,
        search_property: str | typing.Any,
        new: str | typing.Any = "",
        unlink: str | typing.Any = "",
        rows: typing.Any | None = 0,
        cols: typing.Any | None = 0,
    ):
        """template_search_preview

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param search_data: Data from which to take collection to search in
        :type search_data: typing.Any
        :param search_property: Identifier of search collection property
        :type search_property: str | typing.Any
        :param new: Operator identifier to create a new item for the collection
        :type new: str | typing.Any
        :param unlink: Operator identifier to unlink or delete the active item from the collection
        :type unlink: str | typing.Any
        :param rows: Number of thumbnail preview rows to display
        :type rows: typing.Any | None
        :param cols: Number of thumbnail preview columns to display
        :type cols: typing.Any | None
        """
        ...

    def template_path_builder(
        self,
        data: typing.Any,
        property: str | typing.Any,
        root: ID | None,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
    ):
        """template_path_builder

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param root: ID-block from which path is evaluated from
        :type root: ID | None
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        """
        ...

    def template_modifiers(self):
        """Generates the UI layout for the modifier stack"""
        ...

    def template_constraints(
        self, use_bone_constraints: bool | typing.Any | None = True
    ):
        """Generates the panels for the constraint stack

        :param use_bone_constraints: Add panels for bone constraints instead of object constraints
        :type use_bone_constraints: bool | typing.Any | None
        """
        ...

    def template_grease_pencil_modifiers(self):
        """Generates the panels for the grease pencil modifier stack"""
        ...

    def template_shaderfx(self):
        """Generates the panels for the shader effect stack"""
        ...

    def template_greasepencil_color(
        self,
        data: typing.Any,
        property: str | typing.Any,
        rows: typing.Any | None = 0,
        cols: typing.Any | None = 0,
        scale: typing.Any | None = 1.0,
        filter: str | None = "ALL",
    ):
        """template_greasepencil_color

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param rows: Number of thumbnail preview rows to display
        :type rows: typing.Any | None
        :param cols: Number of thumbnail preview columns to display
        :type cols: typing.Any | None
        :param scale: Scale of the image thumbnails
        :type scale: typing.Any | None
        :param filter: Optionally limit the items which can be selected
        :type filter: str | None
        """
        ...

    def template_constraint_header(self, data: Constraint):
        """Generates the header for constraint panels

        :param data: Constraint data
        :type data: Constraint
        """
        ...

    def template_preview(
        self,
        id: ID | None,
        show_buttons: bool | typing.Any | None = True,
        parent: ID | None = None,
        slot: TextureSlot | None = None,
        preview_id: str | typing.Any = "",
    ):
        """Item. A preview window for materials, textures, lights or worlds

        :param id: ID data-block
        :type id: ID | None
        :param show_buttons: Show preview buttons?
        :type show_buttons: bool | typing.Any | None
        :param parent: ID data-block
        :type parent: ID | None
        :param slot: Texture slot
        :type slot: TextureSlot | None
        :param preview_id: Identifier of this preview widget, if not set the ID type will be used (i.e. all previews of materials without explicit ID will have the same size...)
        :type preview_id: str | typing.Any
        """
        ...

    def template_curve_mapping(
        self,
        data: typing.Any,
        property: str | typing.Any,
        type: str | None = "NONE",
        levels: bool | typing.Any | None = False,
        brush: bool | typing.Any | None = False,
        use_negative_slope: bool | typing.Any | None = False,
        show_tone: bool | typing.Any | None = False,
    ):
        """Item. A curve mapping widget used for e.g falloff curves for lights

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param type: Type, Type of curves to display
        :type type: str | None
        :param levels: Show black/white levels
        :type levels: bool | typing.Any | None
        :param brush: Show brush options
        :type brush: bool | typing.Any | None
        :param use_negative_slope: Use a negative slope by default
        :type use_negative_slope: bool | typing.Any | None
        :param show_tone: Show tone options
        :type show_tone: bool | typing.Any | None
        """
        ...

    def template_curveprofile(self, data: typing.Any, property: str | typing.Any):
        """A profile path editor used for custom profiles

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_color_ramp(
        self,
        data: typing.Any,
        property: str | typing.Any,
        expand: bool | typing.Any | None = False,
    ):
        """Item. A color ramp widget

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param expand: Expand button to show more detail
        :type expand: bool | typing.Any | None
        """
        ...

    def template_icon(self, icon_value: int | None, scale: typing.Any | None = 1.0):
        """Display a large icon

        :param icon_value: Icon to display
        :type icon_value: int | None
        :param scale: Scale, Scale the icon size (by the button size)
        :type scale: typing.Any | None
        """
        ...

    def template_icon_view(
        self,
        data: typing.Any,
        property: str | typing.Any,
        show_labels: bool | typing.Any | None = False,
        scale: typing.Any | None = 6.0,
        scale_popup: typing.Any | None = 5.0,
    ):
        """Enum. Large widget showing Icon previews

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param show_labels: Show enum label in preview buttons
        :type show_labels: bool | typing.Any | None
        :param scale: UI Units, Scale the button icon size (by the button size)
        :type scale: typing.Any | None
        :param scale_popup: Scale, Scale the popup icon size (by the button size)
        :type scale_popup: typing.Any | None
        """
        ...

    def template_histogram(self, data: typing.Any, property: str | typing.Any):
        """Item. A histogramm widget to analyze imaga data

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_waveform(self, data: typing.Any, property: str | typing.Any):
        """Item. A waveform widget to analyze imaga data

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_vectorscope(self, data: typing.Any, property: str | typing.Any):
        """Item. A vectorscope widget to analyze imaga data

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_layers(
        self,
        data: typing.Any,
        property: str | typing.Any,
        used_layers_data: typing.Any | None,
        used_layers_property: str | typing.Any,
        active_layer: int | None,
    ):
        """template_layers

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param used_layers_data: Data from which to take property
        :type used_layers_data: typing.Any | None
        :param used_layers_property: Identifier of property in data
        :type used_layers_property: str | typing.Any
        :param active_layer: Active Layer
        :type active_layer: int | None
        """
        ...

    def template_color_picker(
        self,
        data: typing.Any,
        property: str | typing.Any,
        value_slider: bool | typing.Any | None = False,
        lock: bool | typing.Any | None = False,
        lock_luminosity: bool | typing.Any | None = False,
        cubic: bool | typing.Any | None = False,
    ):
        """Item. A color wheel widget to pick colors

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param value_slider: Display the value slider to the right of the color wheel
        :type value_slider: bool | typing.Any | None
        :param lock: Lock the color wheel display to value 1.0 regardless of actual color
        :type lock: bool | typing.Any | None
        :param lock_luminosity: Keep the color at its original vector length
        :type lock_luminosity: bool | typing.Any | None
        :param cubic: Cubic saturation for picking values close to white
        :type cubic: bool | typing.Any | None
        """
        ...

    def template_palette(
        self,
        data: typing.Any,
        property: str | typing.Any,
        color: bool | typing.Any | None = False,
    ):
        """Item. A palette used to pick colors

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param color: Display the colors as colors or values
        :type color: bool | typing.Any | None
        """
        ...

    def template_image_layers(self, image: Image | None, image_user: ImageUser | None):
        """template_image_layers

        :param image:
        :type image: Image | None
        :param image_user:
        :type image_user: ImageUser | None
        """
        ...

    def template_image(
        self,
        data: typing.Any,
        property: str | typing.Any,
        image_user: ImageUser,
        compact: bool | typing.Any | None = False,
        multiview: bool | typing.Any | None = False,
    ):
        """Item(s). User interface for selecting images and their source paths

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param image_user:
        :type image_user: ImageUser
        :param compact: Use more compact layout
        :type compact: bool | typing.Any | None
        :param multiview: Expose Multi-View options
        :type multiview: bool | typing.Any | None
        """
        ...

    def template_image_settings(
        self,
        image_settings: ImageFormatSettings,
        color_management: bool | typing.Any | None = False,
    ):
        """User interface for setting image format options

        :param image_settings:
        :type image_settings: ImageFormatSettings
        :param color_management: Show color management settings
        :type color_management: bool | typing.Any | None
        """
        ...

    def template_image_stereo_3d(self, stereo_3d_format: Stereo3dFormat):
        """User interface for setting image stereo 3d options

        :param stereo_3d_format:
        :type stereo_3d_format: Stereo3dFormat
        """
        ...

    def template_image_views(self, image_settings: ImageFormatSettings):
        """User interface for setting image views output options

        :param image_settings:
        :type image_settings: ImageFormatSettings
        """
        ...

    def template_movieclip(
        self,
        data: typing.Any,
        property: str | typing.Any,
        compact: bool | typing.Any | None = False,
    ):
        """Item(s). User interface for selecting movie clips and their source paths

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param compact: Use more compact layout
        :type compact: bool | typing.Any | None
        """
        ...

    def template_track(self, data: typing.Any, property: str | typing.Any):
        """Item. A movie-track widget to preview tracking image.

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_marker(
        self,
        data: typing.Any,
        property: str | typing.Any,
        clip_user: MovieClipUser,
        track: MovieTrackingTrack,
        compact: bool | typing.Any | None = False,
    ):
        """Item. A widget to control single marker settings.

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param clip_user:
        :type clip_user: MovieClipUser
        :param track:
        :type track: MovieTrackingTrack
        :param compact: Use more compact layout
        :type compact: bool | typing.Any | None
        """
        ...

    def template_movieclip_information(
        self, data: typing.Any, property: str | typing.Any, clip_user: MovieClipUser
    ):
        """Item. Movie clip information data.

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param clip_user:
        :type clip_user: MovieClipUser
        """
        ...

    def template_list(
        self,
        listtype_name: str | typing.Any,
        list_id: str | typing.Any,
        dataptr: typing.Any | None,
        propname: str | typing.Any,
        active_dataptr: typing.Any,
        active_propname: str | typing.Any,
        item_dyntip_propname: str | typing.Any = "",
        rows: typing.Any | None = 5,
        maxrows: typing.Any | None = 5,
        type: str | None = "DEFAULT",
        columns: typing.Any | None = 9,
        sort_reverse: bool | typing.Any | None = False,
        sort_lock: bool | typing.Any | None = False,
    ):
        """Item. A list widget to display data, e.g. vertexgroups.

        :param listtype_name: Identifier of the list type to use
        :type listtype_name: str | typing.Any
        :param list_id: Identifier of this list widget (mandatory when using default "UI_UL_list" class). If this not an empty string, the uilist gets a custom ID, otherwise it takes the name of the class used to define the uilist (for example, if the class name is "OBJECT_UL_vgroups", and list_id is not set by the script, then bl_idname = "OBJECT_UL_vgroups")
        :type list_id: str | typing.Any
        :param dataptr: Data from which to take the Collection property
        :type dataptr: typing.Any | None
        :param propname: Identifier of the Collection property in data
        :type propname: str | typing.Any
        :param active_dataptr: Data from which to take the integer property, index of the active item
        :type active_dataptr: typing.Any
        :param active_propname: Identifier of the integer property in active_data, index of the active item
        :type active_propname: str | typing.Any
        :param item_dyntip_propname: Identifier of a string property in items, to use as tooltip content
        :type item_dyntip_propname: str | typing.Any
        :param rows: Default and minimum number of rows to display
        :type rows: typing.Any | None
        :param maxrows: Default maximum number of rows to display
        :type maxrows: typing.Any | None
        :param type: Type, Type of layout to use
        :type type: str | None
        :param columns: Number of items to display per row, for GRID layout
        :type columns: typing.Any | None
        :param sort_reverse: Display items in reverse order by default
        :type sort_reverse: bool | typing.Any | None
        :param sort_lock: Lock display order to default value
        :type sort_lock: bool | typing.Any | None
        """
        ...

    def template_running_jobs(self):
        """template_running_jobs"""
        ...

    def template_operator_search(self):
        """template_operator_search"""
        ...

    def template_menu_search(self):
        """template_menu_search"""
        ...

    def template_header_3D_mode(self): ...
    def template_edit_mode_selection(self):
        """Inserts common 3DView Edit modes header UI (selector for selection mode)"""
        ...

    def template_reports_banner(self):
        """template_reports_banner"""
        ...

    def template_input_status(self):
        """template_input_status"""
        ...

    def template_status_info(self):
        """template_status_info"""
        ...

    def template_node_link(
        self, ntree: NodeTree | None, node: Node | None, socket: NodeSocket | None
    ):
        """template_node_link

        :param ntree:
        :type ntree: NodeTree | None
        :param node:
        :type node: Node | None
        :param socket:
        :type socket: NodeSocket | None
        """
        ...

    def template_node_view(
        self, ntree: NodeTree | None, node: Node | None, socket: NodeSocket | None
    ):
        """template_node_view

        :param ntree:
        :type ntree: NodeTree | None
        :param node:
        :type node: Node | None
        :param socket:
        :type socket: NodeSocket | None
        """
        ...

    def template_node_asset_menu_items(self, catalog_path: str | typing.Any = ""):
        """template_node_asset_menu_items

        :param catalog_path:
        :type catalog_path: str | typing.Any
        """
        ...

    def template_modifier_asset_menu_items(self, catalog_path: str | typing.Any = ""):
        """template_modifier_asset_menu_items

        :param catalog_path:
        :type catalog_path: str | typing.Any
        """
        ...

    def template_node_operator_asset_menu_items(
        self, catalog_path: str | typing.Any = ""
    ):
        """template_node_operator_asset_menu_items

        :param catalog_path:
        :type catalog_path: str | typing.Any
        """
        ...

    def template_node_operator_asset_root_items(self):
        """template_node_operator_asset_root_items"""
        ...

    def template_texture_user(self):
        """template_texture_user"""
        ...

    def template_keymap_item_properties(self, item: KeyMapItem):
        """template_keymap_item_properties

        :param item:
        :type item: KeyMapItem
        """
        ...

    def template_component_menu(
        self,
        data: typing.Any | None,
        property: str | typing.Any,
        name: str | typing.Any = "",
    ):
        """Item. Display expanded property in a popup menu

        :param data: Data from which to take property
        :type data: typing.Any | None
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param name:
        :type name: str | typing.Any
        """
        ...

    def template_colorspace_settings(
        self, data: typing.Any, property: str | typing.Any
    ):
        """Item. A widget to control input color space settings.

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_colormanaged_view_settings(
        self, data: typing.Any, property: str | typing.Any
    ):
        """Item. A widget to control color managed view settings.

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_node_socket(self, color: typing.Any | None = (0.0, 0.0, 0.0, 1.0)):
        """Node Socket Icon

        :param color: Color
        :type color: typing.Any | None
        """
        ...

    def template_cache_file(self, data: typing.Any, property: str | typing.Any):
        """Item(s). User interface for selecting cache files and their source paths

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_cache_file_velocity(
        self, data: typing.Any, property: str | typing.Any
    ):
        """Show cache files velocity properties

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_cache_file_procedural(
        self, data: typing.Any, property: str | typing.Any
    ):
        """Show cache files render procedural properties

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_cache_file_time_settings(
        self, data: typing.Any, property: str | typing.Any
    ):
        """Show cache files time settings

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_cache_file_layers(self, data: typing.Any, property: str | typing.Any):
        """Show cache files override layers properties

        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_recent_files(self, rows: typing.Any | None = 5) -> int:
        """Show list of recently saved .blend files

        :param rows: Maximum number of items to show
        :type rows: typing.Any | None
        :return: Number of items drawn
        :rtype: int
        """
        ...

    def template_file_select_path(self, params: FileSelectParams | None):
        """Item. A text button to set the active file browser path.

        :param params:
        :type params: FileSelectParams | None
        """
        ...

    def template_event_from_keymap_item(
        self,
        item: KeyMapItem,
        text: str | typing.Any | None = "",
        text_ctxt: str | typing.Any | None = "",
        translate: bool | typing.Any | None = True,
    ):
        """Display keymap item as icons/text

        :param item: Item
        :type item: KeyMapItem
        :param text: Override automatic text of the item
        :type text: str | typing.Any | None
        :param text_ctxt: Override automatic translation context of the given text
        :type text_ctxt: str | typing.Any | None
        :param translate: Translate the given text, when UI translation is enabled
        :type translate: bool | typing.Any | None
        """
        ...

    def template_asset_view(
        self,
        list_id: str | typing.Any,
        asset_library_dataptr: typing.Any,
        asset_library_propname: str | typing.Any,
        assets_dataptr: typing.Any,
        assets_propname: str | typing.Any,
        active_dataptr: typing.Any,
        active_propname: str | typing.Any,
        filter_id_types: set[str] | None = {},
        display_options: set[str] | None = {},
        activate_operator: str | typing.Any = "",
        drag_operator: str | typing.Any = "",
    ):
        """Item. A scrollable list of assets in a grid view

                :param list_id: Identifier of this asset view. Necessary to tell apart different asset views and to idenify an asset view read from a .blend
                :type list_id: str | typing.Any
                :param asset_library_dataptr: Data from which to take the active asset library property
                :type asset_library_dataptr: typing.Any
                :param asset_library_propname: Identifier of the asset library property
                :type asset_library_propname: str | typing.Any
                :param assets_dataptr: Data from which to take the asset list property
                :type assets_dataptr: typing.Any
                :param assets_propname: Identifier of the asset list property
                :type assets_propname: str | typing.Any
                :param active_dataptr: Data from which to take the integer property, index of the active item
                :type active_dataptr: typing.Any
                :param active_propname: Identifier of the integer property in active_data, index of the active item
                :type active_propname: str | typing.Any
                :param filter_id_types: filter_id_types
                :type filter_id_types: set[str] | None
                :param display_options: Displaying options for the asset view

        NO_NAMES
        Do not display the name of each asset underneath preview images.

        NO_FILTER
        Do not display buttons for filtering the available assets.

        NO_LIBRARY
        Do not display buttons to choose or refresh an asset library.
                :type display_options: set[str] | None
                :param activate_operator: Name of a custom operator to invoke when activating an item
                :type activate_operator: str | typing.Any
                :param drag_operator: Name of a custom operator to invoke when starting to drag an item. Never invoked together with the active_operator (if set), it's either the drag or the activate one
                :type drag_operator: str | typing.Any
                :return: activate_operator_properties, Operator properties to fill in for the custom activate operator passed to the template, `OperatorProperties`

        drag_operator_properties, Operator properties to fill in for the custom drag operator passed to the template, `OperatorProperties`
        """
        ...

    def template_light_linking_collection(
        self, context_layout: UILayout, data: typing.Any, property: str | typing.Any
    ):
        """Visualization of a content of a light linking collection

        :param context_layout: Layout to set active list element as context properties
        :type context_layout: UILayout
        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        """
        ...

    def template_bone_collection_tree(self):
        """Show bone collections tree"""
        ...

    def template_node_tree_interface(self, interface: NodeTreeInterface):
        """Show a node tree interface

        :param interface: Node Tree Interface, Interface of a node tree to display
        :type interface: NodeTreeInterface
        """
        ...

    def template_node_inputs(self, node: Node):
        """Show a node settings and input socket values

        :param node: Node, Display inputs of this node
        :type node: Node
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

    def introspect(self):
        """Return a dictionary containing a textual representation of the UI layout."""
        ...
