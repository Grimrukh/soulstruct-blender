import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TransformConstraint(Constraint, bpy_struct):
    """Map transformations of the target to the object"""

    from_max_x: float
    """ Top range of X axis source motion

    :type: float
    """

    from_max_x_rot: float
    """ Top range of X axis source motion

    :type: float
    """

    from_max_x_scale: float
    """ Top range of X axis source motion

    :type: float
    """

    from_max_y: float
    """ Top range of Y axis source motion

    :type: float
    """

    from_max_y_rot: float
    """ Top range of Y axis source motion

    :type: float
    """

    from_max_y_scale: float
    """ Top range of Y axis source motion

    :type: float
    """

    from_max_z: float
    """ Top range of Z axis source motion

    :type: float
    """

    from_max_z_rot: float
    """ Top range of Z axis source motion

    :type: float
    """

    from_max_z_scale: float
    """ Top range of Z axis source motion

    :type: float
    """

    from_min_x: float
    """ Bottom range of X axis source motion

    :type: float
    """

    from_min_x_rot: float
    """ Bottom range of X axis source motion

    :type: float
    """

    from_min_x_scale: float
    """ Bottom range of X axis source motion

    :type: float
    """

    from_min_y: float
    """ Bottom range of Y axis source motion

    :type: float
    """

    from_min_y_rot: float
    """ Bottom range of Y axis source motion

    :type: float
    """

    from_min_y_scale: float
    """ Bottom range of Y axis source motion

    :type: float
    """

    from_min_z: float
    """ Bottom range of Z axis source motion

    :type: float
    """

    from_min_z_rot: float
    """ Bottom range of Z axis source motion

    :type: float
    """

    from_min_z_scale: float
    """ Bottom range of Z axis source motion

    :type: float
    """

    from_rotation_mode: str
    """ Specify the type of rotation channels to use

    :type: str
    """

    map_from: str
    """ The transformation type to use from the target

    :type: str
    """

    map_to: str
    """ The transformation type to affect on the constrained object

    :type: str
    """

    map_to_x_from: str
    """ The source axis constrained object's X axis uses

    :type: str
    """

    map_to_y_from: str
    """ The source axis constrained object's Y axis uses

    :type: str
    """

    map_to_z_from: str
    """ The source axis constrained object's Z axis uses

    :type: str
    """

    mix_mode: str
    """ Specify how to combine the new location with original

    :type: str
    """

    mix_mode_rot: str
    """ Specify how to combine the new rotation with original

    :type: str
    """

    mix_mode_scale: str
    """ Specify how to combine the new scale with original

    :type: str
    """

    subtarget: str
    """ Armature bone, mesh or lattice vertex group, ...

    :type: str
    """

    target: Object
    """ Target object

    :type: Object
    """

    to_euler_order: str
    """ Explicitly specify the output euler rotation order

    :type: str
    """

    to_max_x: float
    """ Top range of X axis destination motion

    :type: float
    """

    to_max_x_rot: float
    """ Top range of X axis destination motion

    :type: float
    """

    to_max_x_scale: float
    """ Top range of X axis destination motion

    :type: float
    """

    to_max_y: float
    """ Top range of Y axis destination motion

    :type: float
    """

    to_max_y_rot: float
    """ Top range of Y axis destination motion

    :type: float
    """

    to_max_y_scale: float
    """ Top range of Y axis destination motion

    :type: float
    """

    to_max_z: float
    """ Top range of Z axis destination motion

    :type: float
    """

    to_max_z_rot: float
    """ Top range of Z axis destination motion

    :type: float
    """

    to_max_z_scale: float
    """ Top range of Z axis destination motion

    :type: float
    """

    to_min_x: float
    """ Bottom range of X axis destination motion

    :type: float
    """

    to_min_x_rot: float
    """ Bottom range of X axis destination motion

    :type: float
    """

    to_min_x_scale: float
    """ Bottom range of X axis destination motion

    :type: float
    """

    to_min_y: float
    """ Bottom range of Y axis destination motion

    :type: float
    """

    to_min_y_rot: float
    """ Bottom range of Y axis destination motion

    :type: float
    """

    to_min_y_scale: float
    """ Bottom range of Y axis destination motion

    :type: float
    """

    to_min_z: float
    """ Bottom range of Z axis destination motion

    :type: float
    """

    to_min_z_rot: float
    """ Bottom range of Z axis destination motion

    :type: float
    """

    to_min_z_scale: float
    """ Bottom range of Z axis destination motion

    :type: float
    """

    use_motion_extrapolate: bool
    """ Extrapolate ranges

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
