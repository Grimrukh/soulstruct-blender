import typing
import collections.abc
import mathutils
from .space import Space
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceOutliner(Space, bpy_struct):
    """Outliner space data"""

    display_mode: str
    """ Type of information to display

    :type: str
    """

    filter_id_type: str
    """ Data-block type to show

    :type: str
    """

    filter_invert: bool
    """ Invert the object state filter

    :type: bool
    """

    filter_state: str
    """ 

    :type: str
    """

    filter_text: str
    """ Live search filtering string

    :type: str
    """

    lib_override_view_mode: str
    """ Choose different visualizations of library override data

    :type: str
    """

    show_mode_column: bool
    """ Show the mode column for mode toggle and activation

    :type: bool
    """

    show_restrict_column_enable: bool
    """ Exclude from view layer

    :type: bool
    """

    show_restrict_column_hide: bool
    """ Temporarily hide in viewport

    :type: bool
    """

    show_restrict_column_holdout: bool
    """ Holdout

    :type: bool
    """

    show_restrict_column_indirect_only: bool
    """ Indirect only

    :type: bool
    """

    show_restrict_column_render: bool
    """ Globally disable in renders

    :type: bool
    """

    show_restrict_column_select: bool
    """ Selectable

    :type: bool
    """

    show_restrict_column_viewport: bool
    """ Globally disable in viewports

    :type: bool
    """

    use_filter_case_sensitive: bool
    """ Only use case sensitive matches of search string

    :type: bool
    """

    use_filter_children: bool
    """ Show children

    :type: bool
    """

    use_filter_collection: bool
    """ Show collections

    :type: bool
    """

    use_filter_complete: bool
    """ Only use complete matches of search string

    :type: bool
    """

    use_filter_id_type: bool
    """ Show only data-blocks of one type

    :type: bool
    """

    use_filter_lib_override_system: bool
    """ For libraries with overrides created, show the overridden values that are defined/controlled automatically (e.g. to make users of an overridden data-block point to the override data, not the original linked data)

    :type: bool
    """

    use_filter_object: bool
    """ Show objects

    :type: bool
    """

    use_filter_object_armature: bool
    """ Show armature objects

    :type: bool
    """

    use_filter_object_camera: bool
    """ Show camera objects

    :type: bool
    """

    use_filter_object_content: bool
    """ Show what is inside the objects elements

    :type: bool
    """

    use_filter_object_empty: bool
    """ Show empty objects

    :type: bool
    """

    use_filter_object_grease_pencil: bool
    """ Show grease pencil objects

    :type: bool
    """

    use_filter_object_light: bool
    """ Show light objects

    :type: bool
    """

    use_filter_object_mesh: bool
    """ Show mesh objects

    :type: bool
    """

    use_filter_object_others: bool
    """ Show curves, lattices, light probes, fonts, ...

    :type: bool
    """

    use_filter_view_layers: bool
    """ Show all the view layers

    :type: bool
    """

    use_sort_alpha: bool
    """ 

    :type: bool
    """

    use_sync_select: bool
    """ Sync outliner selection with other editors

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
