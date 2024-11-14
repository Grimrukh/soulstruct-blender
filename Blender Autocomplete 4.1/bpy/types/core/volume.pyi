import typing
import collections.abc
import mathutils
from .volume_render import VolumeRender
from .struct import Struct
from .bpy_struct import bpy_struct
from .volume_grids import VolumeGrids
from .packed_file import PackedFile
from .anim_data import AnimData
from .id import ID
from .volume_display import VolumeDisplay
from .id_materials import IDMaterials

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Volume(ID, bpy_struct):
    """Volume data-block for 3D volume grids"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    display: VolumeDisplay
    """ Volume display settings for 3D viewport

    :type: VolumeDisplay
    """

    filepath: str
    """ Volume file used by this Volume data-block

    :type: str
    """

    frame_duration: int
    """ Number of frames of the sequence to use

    :type: int
    """

    frame_offset: int
    """ Offset the number of the frame to use in the animation

    :type: int
    """

    frame_start: int
    """ Global starting frame of the sequence, assuming first has a #1

    :type: int
    """

    grids: VolumeGrids
    """ 3D volume grids

    :type: VolumeGrids
    """

    is_sequence: bool
    """ Whether the cache is separated in a series of files

    :type: bool
    """

    materials: IDMaterials
    """ 

    :type: IDMaterials
    """

    packed_file: PackedFile
    """ 

    :type: PackedFile
    """

    render: VolumeRender
    """ Volume render settings for 3D viewport

    :type: VolumeRender
    """

    sequence_mode: str
    """ Sequence playback mode

    :type: str
    """

    velocity_grid: str
    """ Name of the velocity field, or the base name if the velocity is split into multiple grids

    :type: str
    """

    velocity_scale: float
    """ Factor to control the amount of motion blur

    :type: float
    """

    velocity_unit: str
    """ Define how the velocity vectors are interpreted with regard to time, 'frame' means the delta time is 1 frame, 'second' means the delta time is 1 / FPS

    :type: str
    """

    velocity_x_grid: str
    """ Name of the grid for the X axis component of the velocity field if it was split into multiple grids

    :type: str
    """

    velocity_y_grid: str
    """ Name of the grid for the Y axis component of the velocity field if it was split into multiple grids

    :type: str
    """

    velocity_z_grid: str
    """ Name of the grid for the Z axis component of the velocity field if it was split into multiple grids

    :type: str
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
