import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .constraint_target import ConstraintTarget
from .text import Text

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PythonConstraint(Constraint, bpy_struct):
    """Use Python script for constraint evaluation"""

    has_script_error: bool
    """ The linked Python script has thrown an error

    :type: bool
    """

    target_count: int
    """ Usually only 1 to 3 are needed

    :type: int
    """

    targets: bpy_prop_collection[ConstraintTarget]
    """ Target Objects

    :type: bpy_prop_collection[ConstraintTarget]
    """

    text: Text
    """ The text object that contains the Python script

    :type: Text
    """

    use_targets: bool
    """ Use the targets indicated in the constraint panel

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
