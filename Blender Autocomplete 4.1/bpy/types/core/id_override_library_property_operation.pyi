import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class IDOverrideLibraryPropertyOperation(bpy_struct):
    """Description of an override operation over an overridden property"""

    flag: set[str]
    """ Status flags

    :type: set[str]
    """

    operation: str
    """ What override operation is performed

    :type: str
    """

    subitem_local_id: ID
    """ Collection of IDs only, used to disambiguate between potential IDs with same name from different libraries

    :type: ID
    """

    subitem_local_index: int
    """ Used to handle changes into collection

    :type: int
    """

    subitem_local_name: str
    """ Used to handle changes into collection

    :type: str
    """

    subitem_reference_id: ID
    """ Collection of IDs only, used to disambiguate between potential IDs with same name from different libraries

    :type: ID
    """

    subitem_reference_index: int
    """ Used to handle changes into collection

    :type: int
    """

    subitem_reference_name: str
    """ Used to handle changes into collection

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
