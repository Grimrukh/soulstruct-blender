import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .curve_mapping import CurveMapping
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class HookModifier(Modifier, bpy_struct):
    """Hook modifier to modify the location of vertices"""

    center: mathutils.Vector
    """ Center of the hook, used for falloff and display

    :type: mathutils.Vector
    """

    falloff_curve: CurveMapping
    """ Custom falloff curve

    :type: CurveMapping
    """

    falloff_radius: float
    """ If not zero, the distance from the hook where influence ends

    :type: float
    """

    falloff_type: str
    """ 

    :type: str
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    matrix_inverse: mathutils.Matrix
    """ Reverse the transformation between this object and its target

    :type: mathutils.Matrix
    """

    object: Object
    """ Parent Object for hook, also recalculates and clears offset

    :type: Object
    """

    strength: float
    """ Relative force of the hook

    :type: float
    """

    subtarget: str
    """ Name of Parent Bone for hook (if applicable), also recalculates and clears offset

    :type: str
    """

    use_falloff_uniform: bool
    """ Compensate for non-uniform object scale

    :type: bool
    """

    vertex_group: str
    """ Name of Vertex Group which determines influence of modifier per point

    :type: str
    """

    vertex_indices: bpy_prop_array[int]
    """ Indices of vertices bound to the modifier. For Bézier curves, handles count as additional vertices

    :type: bpy_prop_array[int]
    """

    def vertex_indices_set(self, indices: collections.abc.Iterable[int] | None):
        """Validates and assigns the array of vertex indices bound to the modifier

        :param indices: Vertex Indices
        :type indices: collections.abc.Iterable[int] | None
        """
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
