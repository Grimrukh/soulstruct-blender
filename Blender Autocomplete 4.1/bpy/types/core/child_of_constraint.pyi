import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ChildOfConstraint(Constraint, bpy_struct):
    """Create constraint-based parent-child relationship"""

    inverse_matrix: mathutils.Matrix
    """ Transformation matrix to apply before

    :type: mathutils.Matrix
    """

    set_inverse_pending: bool
    """ Set to true to request recalculation of the inverse matrix

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

    use_location_x: bool
    """ Use X Location of Parent

    :type: bool
    """

    use_location_y: bool
    """ Use Y Location of Parent

    :type: bool
    """

    use_location_z: bool
    """ Use Z Location of Parent

    :type: bool
    """

    use_rotation_x: bool
    """ Use X Rotation of Parent

    :type: bool
    """

    use_rotation_y: bool
    """ Use Y Rotation of Parent

    :type: bool
    """

    use_rotation_z: bool
    """ Use Z Rotation of Parent

    :type: bool
    """

    use_scale_x: bool
    """ Use X Scale of Parent

    :type: bool
    """

    use_scale_y: bool
    """ Use Y Scale of Parent

    :type: bool
    """

    use_scale_z: bool
    """ Use Z Scale of Parent

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
