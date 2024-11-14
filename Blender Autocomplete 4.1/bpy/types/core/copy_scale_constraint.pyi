import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CopyScaleConstraint(Constraint, bpy_struct):
    """Copy the scale of the target"""

    power: float
    """ Raise the target's scale to the specified power

    :type: float
    """

    subtarget: str
    """ Armature bone, mesh or lattice vertex group, ...

    :type: str
    """

    target: Object
    """ Target object

    :type: Object
    """

    use_add: bool
    """ Use addition instead of multiplication to combine scale (2.7 compatibility)

    :type: bool
    """

    use_make_uniform: bool
    """ Redistribute the copied change in volume equally between the three axes of the owner

    :type: bool
    """

    use_offset: bool
    """ Combine original scale with copied scale

    :type: bool
    """

    use_x: bool
    """ Copy the target's X scale

    :type: bool
    """

    use_y: bool
    """ Copy the target's Y scale

    :type: bool
    """

    use_z: bool
    """ Copy the target's Z scale

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
