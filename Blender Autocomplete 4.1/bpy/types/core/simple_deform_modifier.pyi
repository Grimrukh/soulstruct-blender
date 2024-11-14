import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SimpleDeformModifier(Modifier, bpy_struct):
    """Simple deformation modifier to apply effects such as twisting and bending"""

    angle: float
    """ Angle of deformation

    :type: float
    """

    deform_axis: str
    """ Deform around local axis

    :type: str
    """

    deform_method: str
    """ 

    :type: str
    """

    factor: float
    """ Amount to deform object

    :type: float
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    limits: bpy_prop_array[float]
    """ Lower/Upper limits for deform

    :type: bpy_prop_array[float]
    """

    lock_x: bool
    """ Do not allow deformation along the X axis

    :type: bool
    """

    lock_y: bool
    """ Do not allow deformation along the Y axis

    :type: bool
    """

    lock_z: bool
    """ Do not allow deformation along the Z axis

    :type: bool
    """

    origin: Object
    """ Offset the origin and orientation of the deformation

    :type: Object
    """

    vertex_group: str
    """ Vertex group name

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
