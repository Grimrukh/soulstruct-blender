import typing
import collections.abc
import mathutils
from .struct import Struct
from .cloth_solver_result import ClothSolverResult
from .cloth_settings import ClothSettings
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .cloth_collision_settings import ClothCollisionSettings
from .point_cache import PointCache
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ClothModifier(Modifier, bpy_struct):
    """Cloth simulation modifier"""

    collision_settings: ClothCollisionSettings
    """ 

    :type: ClothCollisionSettings
    """

    hair_grid_max: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    hair_grid_min: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    hair_grid_resolution: bpy_prop_array[int]
    """ 

    :type: bpy_prop_array[int]
    """

    point_cache: PointCache
    """ 

    :type: PointCache
    """

    settings: ClothSettings
    """ 

    :type: ClothSettings
    """

    solver_result: ClothSolverResult
    """ 

    :type: ClothSolverResult
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
