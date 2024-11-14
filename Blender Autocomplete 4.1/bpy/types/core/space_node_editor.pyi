import typing
import collections.abc
import mathutils
from .space import Space
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .space_node_overlay import SpaceNodeOverlay
from .space_node_editor_path import SpaceNodeEditorPath
from .id import ID
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceNodeEditor(Space, bpy_struct):
    """Node editor space data"""

    backdrop_channels: str
    """ Channels of the image to draw

    :type: str
    """

    backdrop_offset: bpy_prop_array[float]
    """ Backdrop offset

    :type: bpy_prop_array[float]
    """

    backdrop_zoom: float
    """ Backdrop zoom factor

    :type: float
    """

    cursor_location: mathutils.Vector
    """ Location for adding new nodes

    :type: mathutils.Vector
    """

    edit_tree: NodeTree
    """ Node tree being displayed and edited

    :type: NodeTree
    """

    geometry_nodes_tool_tree: NodeTree
    """ Node group to edit as node tool

    :type: NodeTree
    """

    geometry_nodes_type: str
    """ 

    :type: str
    """

    id: ID
    """ Data-block whose nodes are being edited

    :type: ID
    """

    id_from: ID
    """ Data-block from which the edited data-block is linked

    :type: ID
    """

    insert_offset_direction: str
    """ Direction to offset nodes on insertion

    :type: str
    """

    node_tree: NodeTree
    """ Base node tree from context

    :type: NodeTree
    """

    overlay: SpaceNodeOverlay
    """ Settings for display of overlays in the Node Editor

    :type: SpaceNodeOverlay
    """

    path: SpaceNodeEditorPath
    """ Path from the data-block to the currently edited node tree

    :type: SpaceNodeEditorPath
    """

    pin: bool
    """ Use the pinned node tree

    :type: bool
    """

    shader_type: str
    """ Type of data to take shader from

    :type: str
    """

    show_annotation: bool
    """ Show annotations for this view

    :type: bool
    """

    show_backdrop: bool
    """ Use active Viewer Node output as backdrop for compositing nodes

    :type: bool
    """

    show_region_toolbar: bool
    """ 

    :type: bool
    """

    show_region_ui: bool
    """ 

    :type: bool
    """

    supports_previews: bool
    """ Whether the node editor's type supports displaying node previews

    :type: bool
    """

    texture_type: str
    """ Type of data to take texture from

    :type: str
    """

    tree_type: str
    """ Node tree type to display and edit

    :type: str
    """

    use_auto_render: bool
    """ Re-render and composite changed layers on 3D edits

    :type: bool
    """

    def cursor_location_from_region(self, x: int | None, y: int | None):
        """Set the cursor location using region coordinates

        :param x: x, Region x coordinate
        :type x: int | None
        :param y: y, Region y coordinate
        :type y: int | None
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
    def draw_handler_add(
        cls,
        callback: typing.Any | None,
        args: tuple | None,
        region_type: str | None,
        draw_type: str | None,
    ) -> typing.Any:
        """Add a new draw handler to this space type.
        It will be called every time the specified region in the space type will be drawn.
        Note: All arguments are positional only for now.

                :param callback: A function that will be called when the region is drawn.
        It gets the specified arguments as input.
                :type callback: typing.Any | None
                :param args: Arguments that will be passed to the callback.
                :type args: tuple | None
                :param region_type: The region type the callback draws in; usually WINDOW. (`bpy.types.Region.type`)
                :type region_type: str | None
                :param draw_type: Usually POST_PIXEL for 2D drawing and POST_VIEW for 3D drawing. In some cases PRE_VIEW can be used. BACKDROP can be used for backdrops in the node editor.
                :type draw_type: str | None
                :return: Handler that can be removed later on.
                :rtype: typing.Any
        """
        ...

    @classmethod
    def draw_handler_remove(cls, handler: typing.Any | None, region_type: str | None):
        """Remove a draw handler that was added previously.

        :param handler: The draw handler that should be removed.
        :type handler: typing.Any | None
        :param region_type: Region type the callback was added to.
        :type region_type: str | None
        """
        ...
