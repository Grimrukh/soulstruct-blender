import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CopyRotationConstraint(Constraint, bpy_struct):
    """Copy the rotation of the target"""

    euler_order: str
    """ Explicitly specify the euler rotation order

    :type: str
    """

    invert_x: bool
    """ Invert the X rotation

    :type: bool
    """

    invert_y: bool
    """ Invert the Y rotation

    :type: bool
    """

    invert_z: bool
    """ Invert the Z rotation

    :type: bool
    """

    mix_mode: str
    """ Specify how the copied and existing rotations are combined

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

    use_offset: bool
    """ DEPRECATED: Add original rotation into copied rotation

    :type: bool
    """

    use_x: bool
    """ Copy the target's X rotation

    :type: bool
    """

    use_y: bool
    """ Copy the target's Y rotation

    :type: bool
    """

    use_z: bool
    """ Copy the target's Z rotation

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
