import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CopyLocationConstraint(Constraint, bpy_struct):
    """Copy the location of the target"""

    head_tail: float
    """ Target along length of bone: Head is 0, Tail is 1

    :type: float
    """

    invert_x: bool
    """ Invert the X location

    :type: bool
    """

    invert_y: bool
    """ Invert the Y location

    :type: bool
    """

    invert_z: bool
    """ Invert the Z location

    :type: bool
    """

    subtarget: str
    """ Armature bone, mesh or lattice vertex group, ...

    :type: str
    """

    target: Object
    """ Target object

    :type: Object
    """

    use_bbone_shape: bool
    """ Follow shape of B-Bone segments when calculating Head/Tail position

    :type: bool
    """

    use_offset: bool
    """ Add original location into copied location

    :type: bool
    """

    use_x: bool
    """ Copy the target's X location

    :type: bool
    """

    use_y: bool
    """ Copy the target's Y location

    :type: bool
    """

    use_z: bool
    """ Copy the target's Z location

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
