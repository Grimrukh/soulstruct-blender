import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BooleanModifier(Modifier, bpy_struct):
    """Boolean operations modifier"""

    collection: Collection
    """ Use mesh objects in this collection for Boolean operation

    :type: Collection
    """

    debug_options: set[str]
    """ Debugging options, only when started with '-d'

    :type: set[str]
    """

    double_threshold: float
    """ Threshold for checking overlapping geometry

    :type: float
    """

    material_mode: str
    """ Method for setting materials on the new faces

    :type: str
    """

    object: Object
    """ Mesh object to use for Boolean operation

    :type: Object
    """

    operand_type: str
    """ 

    :type: str
    """

    operation: str
    """ 

    :type: str
    """

    solver: str
    """ Method for calculating booleans

    :type: str
    """

    use_hole_tolerant: bool
    """ Better results when there are holes (slower)

    :type: bool
    """

    use_self: bool
    """ Allow self-intersection in operands

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
