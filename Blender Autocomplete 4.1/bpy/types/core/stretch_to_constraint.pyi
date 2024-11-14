import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class StretchToConstraint(Constraint, bpy_struct):
    """Stretch to meet the target object"""

    bulge: float
    """ Factor between volume variation and stretching

    :type: float
    """

    bulge_max: float
    """ Maximum volume stretching factor

    :type: float
    """

    bulge_min: float
    """ Minimum volume stretching factor

    :type: float
    """

    bulge_smooth: float
    """ Strength of volume stretching clamping

    :type: float
    """

    head_tail: float
    """ Target along length of bone: Head is 0, Tail is 1

    :type: float
    """

    keep_axis: str
    """ The rotation type and axis order to use

    :type: str
    """

    rest_length: float
    """ Length at rest position

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

    use_bbone_shape: bool
    """ Follow shape of B-Bone segments when calculating Head/Tail position

    :type: bool
    """

    use_bulge_max: bool
    """ Use upper limit for volume variation

    :type: bool
    """

    use_bulge_min: bool
    """ Use lower limit for volume variation

    :type: bool
    """

    volume: str
    """ Maintain the object's volume as it stretches

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
