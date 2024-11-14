import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ImageUser(bpy_struct):
    """Parameters defining how an Image data-block is used by another data-block"""

    frame_current: int
    """ Current frame number in image sequence or movie

    :type: int
    """

    frame_duration: int
    """ Number of images of a movie to use

    :type: int
    """

    frame_offset: int
    """ Offset the number of the frame to use in the animation

    :type: int
    """

    frame_start: int
    """ Global starting frame of the movie/sequence, assuming first picture has a #1

    :type: int
    """

    multilayer_layer: int
    """ Layer in multilayer image

    :type: int
    """

    multilayer_pass: int
    """ Pass in multilayer image

    :type: int
    """

    multilayer_view: int
    """ View in multilayer image

    :type: int
    """

    tile: int
    """ Tile in tiled image

    :type: int
    """

    use_auto_refresh: bool
    """ Always refresh image on frame changes

    :type: bool
    """

    use_cyclic: bool
    """ Cycle the images in the movie

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
