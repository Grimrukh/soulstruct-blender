import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .shape_key import ShapeKey
from .anim_data import AnimData
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Key(ID, bpy_struct):
    """Shape keys data-block containing different shapes of geometric data-blocks"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    eval_time: float
    """ Evaluation time for absolute shape keys

    :type: float
    """

    key_blocks: bpy_prop_collection[ShapeKey]
    """ Shape keys

    :type: bpy_prop_collection[ShapeKey]
    """

    reference_key: ShapeKey
    """ 

    :type: ShapeKey
    """

    use_relative: bool
    """ Make shape keys relative, otherwise play through shapes as a sequence using the evaluation time

    :type: bool
    """

    user: ID
    """ Data-block using these shape keys

    :type: ID
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
