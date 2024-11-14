import typing
import collections.abc
import mathutils
from .gizmo_properties import GizmoProperties
from .struct import Struct
from .bpy_struct import bpy_struct
from .operator_properties import OperatorProperties
from .gizmo_group import GizmoGroup
from .context import Context
from .event import Event

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Gizmo(bpy_struct):
    """Collection of gizmos"""

    alpha: float
    """ 

    :type: float
    """

    alpha_highlight: float
    """ 

    :type: float
    """

    bl_idname: str
    """ 

    :type: str
    """

    color: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    color_highlight: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    group: GizmoGroup
    """ Gizmo group this gizmo is a member of

    :type: GizmoGroup
    """

    hide: bool
    """ 

    :type: bool
    """

    hide_keymap: bool
    """ Ignore the key-map for this gizmo

    :type: bool
    """

    hide_select: bool
    """ 

    :type: bool
    """

    is_highlight: bool
    """ 

    :type: bool
    """

    is_modal: bool
    """ 

    :type: bool
    """

    line_width: float
    """ 

    :type: float
    """

    matrix_basis: mathutils.Matrix
    """ 

    :type: mathutils.Matrix
    """

    matrix_offset: mathutils.Matrix
    """ 

    :type: mathutils.Matrix
    """

    matrix_space: mathutils.Matrix
    """ 

    :type: mathutils.Matrix
    """

    matrix_world: mathutils.Matrix
    """ 

    :type: mathutils.Matrix
    """

    properties: GizmoProperties
    """ 

    :type: GizmoProperties
    """

    scale_basis: float
    """ 

    :type: float
    """

    select: bool
    """ 

    :type: bool
    """

    select_bias: float
    """ Depth bias used for selection

    :type: float
    """

    use_draw_hover: bool
    """ 

    :type: bool
    """

    use_draw_modal: bool
    """ Show while dragging

    :type: bool
    """

    use_draw_offset_scale: bool
    """ Scale the offset matrix (use to apply screen-space offset)

    :type: bool
    """

    use_draw_scale: bool
    """ Use scale when calculating the matrix

    :type: bool
    """

    use_draw_value: bool
    """ Show an indicator for the current value while dragging

    :type: bool
    """

    use_event_handle_all: bool
    """ When highlighted, do not pass events through to be handled by other keymaps

    :type: bool
    """

    use_grab_cursor: bool
    """ 

    :type: bool
    """

    use_operator_tool_properties: bool
    """ Merge active tool properties on activation (does not overwrite existing)

    :type: bool
    """

    use_select_background: bool
    """ Don't write into the depth buffer

    :type: bool
    """

    use_tooltip: bool
    """ Use tooltips when hovering over this gizmo

    :type: bool
    """

    def draw(self, context: Context):
        """

        :param context:
        :type context: Context
        """
        ...

    def draw_select(self, context: Context, select_id: typing.Any | None = 0):
        """

        :param context:
        :type context: Context
        :param select_id:
        :type select_id: typing.Any | None
        """
        ...

    def test_select(self, context: Context, location: typing.Any) -> int:
        """

        :param context:
        :type context: Context
        :param location: Location, Region coordinates
        :type location: typing.Any
        :return: Use -1 to skip this gizmo
        :rtype: int
        """
        ...

    def modal(self, context: Context, event: Event, tweak: set[str] | None):
        """

        :param context:
        :type context: Context
        :param event:
        :type event: Event
        :param tweak: Tweak
        :type tweak: set[str] | None
        :return: result
        """
        ...

    def setup(self): ...
    def invoke(self, context: Context, event: Event):
        """

        :param context:
        :type context: Context
        :param event:
        :type event: Event
        :return: result
        """
        ...

    def exit(self, context: Context, cancel: bool | None):
        """

        :param context:
        :type context: Context
        :param cancel: Cancel, otherwise confirm
        :type cancel: bool | None
        """
        ...

    def select_refresh(self): ...
    def draw_preset_box(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        select_id: typing.Any | None = -1,
    ):
        """Draw a box

        :param matrix: The matrix to transform
        :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
        :param select_id: ID to use when gizmo is selectable. Use -1 when not selecting
        :type select_id: typing.Any | None
        """
        ...

    def draw_preset_arrow(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        axis: str | None = "POS_Z",
        select_id: typing.Any | None = -1,
    ):
        """Draw a box

        :param matrix: The matrix to transform
        :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
        :param axis: Arrow Orientation
        :type axis: str | None
        :param select_id: ID to use when gizmo is selectable. Use -1 when not selecting
        :type select_id: typing.Any | None
        """
        ...

    def draw_preset_circle(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        axis: str | None = "POS_Z",
        select_id: typing.Any | None = -1,
    ):
        """Draw a box

        :param matrix: The matrix to transform
        :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
        :param axis: Arrow Orientation
        :type axis: str | None
        :param select_id: ID to use when gizmo is selectable. Use -1 when not selecting
        :type select_id: typing.Any | None
        """
        ...

    def target_set_prop(
        self,
        target: str | typing.Any,
        data: typing.Any,
        property: str | typing.Any,
        index: typing.Any | None = -1,
    ):
        """

        :param target: Target property
        :type target: str | typing.Any
        :param data: Data from which to take property
        :type data: typing.Any
        :param property: Identifier of property in data
        :type property: str | typing.Any
        :param index:
        :type index: typing.Any | None
        """
        ...

    def target_set_operator(
        self, operator: str | typing.Any, index: typing.Any | None = 0
    ) -> OperatorProperties:
        """Operator to run when activating the gizmo (overrides property targets)

        :param operator: Target operator
        :type operator: str | typing.Any
        :param index: Part index
        :type index: typing.Any | None
        :return: Operator properties to fill in
        :rtype: OperatorProperties
        """
        ...

    def target_is_valid(self, property: str | typing.Any) -> bool:
        """

        :param property: Property identifier
        :type property: str | typing.Any
        :return:
        :rtype: bool
        """
        ...

    def draw_custom_shape(
        self,
        shape,
        *,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None = None,
        select_id=None,
    ):
        """Draw a shape created form `Gizmo.draw_custom_shape`.

                :param shape: The cached shape to draw.
                :param matrix: 4x4 matrix, when not given `Gizmo.matrix_world` is used.
                :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
                :param select_id: The selection id.
        Only use when drawing within `Gizmo.draw_select`.
        """
        ...

    @staticmethod
    def new_custom_shape(type: str | None, verts):
        """Create a new shape that can be passed to `Gizmo.draw_custom_shape`.

        :param type: The type of shape to create in (POINTS, LINES, TRIS, LINE_STRIP).
        :type type: str | None
        :param verts: Coordinates.
        :return: The newly created shape.
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

    def target_get_range(self, target):
        """Get the range for this target property.

        :param target: Target property name.
        :return: The range of this property (min, max).
        """
        ...

    def target_get_value(self, target: str | None):
        """Get the value of this target property.

        :param target: Target property name.
        :type target: str | None
        :return: The value of the target property.
        """
        ...

    def target_set_handler(
        self,
        target: str | None,
        get: collections.abc.Callable | None,
        set: collections.abc.Callable | None,
        range: collections.abc.Callable | None = None,
    ):
        """Assigns callbacks to a gizmos property.

        :param target: Target property name.
        :type target: str | None
        :param get: Function that returns the value for this property (single value or sequence).
        :type get: collections.abc.Callable | None
        :param set: Function that takes a single value argument and applies it.
        :type set: collections.abc.Callable | None
        :param range: Function that returns a (min, max) tuple for gizmos that use a range.
        :type range: collections.abc.Callable | None
        """
        ...

    def target_set_value(self, target: str | None):
        """Set the value of this target property.

        :param target: Target property name.
        :type target: str | None
        """
        ...
