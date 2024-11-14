import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .asset_representation import AssetRepresentation
from .context import Context
from .ui_layout import UILayout

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AssetShelf(bpy_struct):
    """Regions for quick access to assets"""

    asset_library_reference: str
    """ Choose the asset library to display assets from

    :type: str
    """

    bl_idname: str
    """ If this is set, the asset gets a custom ID, otherwise it takes the name of the class used to define the asset (for example, if the class name is "OBJECT_AST_hello", and bl_idname is not set by the script, then bl_idname = "OBJECT_AST_hello")

    :type: str
    """

    bl_options: set[str]
    """ Options for this asset shelf type

    :type: set[str]
    """

    bl_space_type: str
    """ The space where the asset shelf is going to be used in

    :type: str
    """

    preview_size: int
    """ Size of the asset preview thumbnails in pixels

    :type: int
    """

    search_filter: str
    """ Filter assets by name

    :type: str
    """

    show_names: bool
    """ Show the asset name together with the preview. Otherwise only the preview will be visible

    :type: bool
    """

    @classmethod
    def poll(cls, context: Context | None) -> bool:
        """If this method returns a non-null output, the asset shelf will be visible

        :param context:
        :type context: Context | None
        :return:
        :rtype: bool
        """
        ...

    @classmethod
    def asset_poll(cls, asset: AssetRepresentation | None) -> bool:
        """Determine if an asset should be visible in the asset shelf. If this method returns a non-null output, the asset will be visible

        :param asset:
        :type asset: AssetRepresentation | None
        :return:
        :rtype: bool
        """
        ...

    @classmethod
    def draw_context_menu(
        cls,
        context: Context | None,
        asset: AssetRepresentation | None,
        layout: UILayout | None,
    ):
        """Draw UI elements into the context menu UI layout displayed on right click

        :param context:
        :type context: Context | None
        :param asset:
        :type asset: AssetRepresentation | None
        :param layout:
        :type layout: UILayout | None
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
