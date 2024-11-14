import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ClothSolverResult(bpy_struct):
    """Result of cloth solver iteration"""

    avg_error: float
    """ Average error during substeps

    :type: float
    """

    avg_iterations: float
    """ Average iterations during substeps

    :type: float
    """

    max_error: float
    """ Maximum error during substeps

    :type: float
    """

    max_iterations: int
    """ Maximum iterations during substeps

    :type: int
    """

    min_error: float
    """ Minimum error during substeps

    :type: float
    """

    min_iterations: int
    """ Minimum iterations during substeps

    :type: int
    """

    status: set[str]
    """ Status of the solver iteration

    :type: set[str]
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
