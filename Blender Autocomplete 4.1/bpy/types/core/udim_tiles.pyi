import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .udim_tile import UDIMTile
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class UDIMTiles(bpy_prop_collection[UDIMTile], bpy_struct):
    """Collection of UDIM tiles"""

    active: UDIMTile
    """ Active Image Tile

    :type: UDIMTile
    """

    active_index: int | None
    """ Active index in tiles array

    :type: int | None
    """

    def new(self, tile_number: int | None, label: str | typing.Any = "") -> UDIMTile:
        """Add a tile to the image

        :param tile_number: Number of the newly created tile
        :type tile_number: int | None
        :param label: Optional label for the tile
        :type label: str | typing.Any
        :return: Newly created image tile
        :rtype: UDIMTile
        """
        ...

    def get(self, tile_number: int | None) -> UDIMTile:
        """Get a tile based on its tile number

        :param tile_number: Number of the tile
        :type tile_number: int | None
        :return: The tile
        :rtype: UDIMTile
        """
        ...

    def remove(self, tile: UDIMTile):
        """Remove an image tile

        :param tile: Image tile to remove
        :type tile: UDIMTile
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
