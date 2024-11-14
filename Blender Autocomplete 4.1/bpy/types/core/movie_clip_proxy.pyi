import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieClipProxy(bpy_struct):
    """Proxy parameters for a movie clip"""

    build_100: bool
    """ Build proxy resolution 100% of the original footage dimension

    :type: bool
    """

    build_25: bool
    """ Build proxy resolution 25% of the original footage dimension

    :type: bool
    """

    build_50: bool
    """ Build proxy resolution 50% of the original footage dimension

    :type: bool
    """

    build_75: bool
    """ Build proxy resolution 75% of the original footage dimension

    :type: bool
    """

    build_free_run: bool
    """ Build free run time code index

    :type: bool
    """

    build_free_run_rec_date: bool
    """ Build free run time code index using Record Date/Time

    :type: bool
    """

    build_record_run: bool
    """ Build record run time code index

    :type: bool
    """

    build_undistorted_100: bool
    """ Build proxy resolution 100% of the original undistorted footage dimension

    :type: bool
    """

    build_undistorted_25: bool
    """ Build proxy resolution 25% of the original undistorted footage dimension

    :type: bool
    """

    build_undistorted_50: bool
    """ Build proxy resolution 50% of the original undistorted footage dimension

    :type: bool
    """

    build_undistorted_75: bool
    """ Build proxy resolution 75% of the original undistorted footage dimension

    :type: bool
    """

    directory: str
    """ Location to store the proxy files

    :type: str
    """

    quality: int
    """ JPEG quality of proxy images

    :type: int
    """

    timecode: str
    """ 

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
