import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .key import Key
from .lattice_point import LatticePoint
from .struct import Struct
from .bpy_struct import bpy_struct
from .anim_data import AnimData
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Lattice(ID, bpy_struct):
    """Lattice data-block defining a grid for deforming other objects"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    interpolation_type_u: str
    """ 

    :type: str
    """

    interpolation_type_v: str
    """ 

    :type: str
    """

    interpolation_type_w: str
    """ 

    :type: str
    """

    is_editmode: bool
    """ True when used in editmode

    :type: bool
    """

    points: bpy_prop_collection[LatticePoint]
    """ Points of the lattice

    :type: bpy_prop_collection[LatticePoint]
    """

    points_u: int
    """ Points in U direction (cannot be changed when there are shape keys)

    :type: int
    """

    points_v: int
    """ Points in V direction (cannot be changed when there are shape keys)

    :type: int
    """

    points_w: int
    """ Points in W direction (cannot be changed when there are shape keys)

    :type: int
    """

    shape_keys: Key
    """ 

    :type: Key
    """

    use_outside: bool
    """ Only display and take into account the outer vertices

    :type: bool
    """

    vertex_group: str
    """ Vertex group to apply the influence of the lattice

    :type: str
    """

    def transform(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
        shape_keys: bool | typing.Any | None = False,
    ):
        """Transform lattice by a matrix

        :param matrix: Matrix
        :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
        :param shape_keys: Transform Shape Keys
        :type shape_keys: bool | typing.Any | None
        """
        ...

    def update_gpu_tag(self):
        """update_gpu_tag"""
        ...

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
