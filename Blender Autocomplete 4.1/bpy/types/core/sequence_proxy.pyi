import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequenceProxy(bpy_struct):
    """Proxy parameters for a sequence strip"""

    build_100: bool
    """ Build 100% proxy resolution

    :type: bool
    """

    build_25: bool
    """ Build 25% proxy resolution

    :type: bool
    """

    build_50: bool
    """ Build 50% proxy resolution

    :type: bool
    """

    build_75: bool
    """ Build 75% proxy resolution

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

    directory: str
    """ Location to store the proxy files

    :type: str
    """

    filepath: str
    """ Location of custom proxy file

    :type: str
    """

    quality: int
    """ Quality of proxies to build

    :type: int
    """

    timecode: str
    """ Method for reading the inputs timecode

    :type: str
    """

    use_overwrite: bool
    """ Overwrite existing proxy files when building

    :type: bool
    """

    use_proxy_custom_directory: bool
    """ Use a custom directory to store data

    :type: bool
    """

    use_proxy_custom_file: bool
    """ Use a custom file to read proxy data from

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
