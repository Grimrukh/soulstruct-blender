import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .volume_grid import VolumeGrid

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VolumeGrids(bpy_prop_collection[VolumeGrid], bpy_struct):
    """3D volume grids"""

    active_index: int | None
    """ Index of active volume grid

    :type: int | None
    """

    error_message: str
    """ If loading grids failed, error message with details

    :type: str
    """

    frame: int
    """ Frame number that volume grids will be loaded at, based on scene time and volume parameters

    :type: int
    """

    frame_filepath: str
    """ Volume file used for loading the volume at the current frame. Empty if the volume has not be loaded or the frame only exists in memory

    :type: str
    """

    is_loaded: bool
    """ List of grids and metadata are loaded in memory

    :type: bool
    """

    def load(self) -> bool:
        """Load list of grids and metadata from file

        :return: True if grid list was successfully loaded
        :rtype: bool
        """
        ...

    def unload(self):
        """Unload all grid and voxel data from memory"""
        ...

    def save(self, filepath: str | typing.Any) -> bool:
        """Save grids and metadata to file

        :param filepath: File path to save to
        :type filepath: str | typing.Any
        :return: True if grid list was successfully loaded
        :rtype: bool
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
