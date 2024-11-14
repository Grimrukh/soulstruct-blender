import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieClipUser(bpy_struct):
    """Parameters defining how a MovieClip data-block is used by another data-block"""

    frame_current: int
    """ Current frame number in movie or image sequence

    :type: int
    """

    proxy_render_size: str
    """ Display preview using full resolution or different proxy resolutions

    :type: str
    """

    use_render_undistorted: bool
    """ Render preview using undistorted proxy

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
