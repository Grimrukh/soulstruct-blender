import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SplineIKConstraint(Constraint, bpy_struct):
    """Align 'n' bones along a curve"""

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

    chain_count: int
    """ How many bones are included in the chain

    :type: int
    """

    joint_bindings: bpy_prop_array[float]
    """ (EXPERIENCED USERS ONLY) The relative positions of the joints along the chain, as percentages

    :type: bpy_prop_array[float]
    """

    target: Object
    """ Curve that controls this relationship

    :type: Object
    """

    use_bulge_max: bool
    """ Use upper limit for volume variation

    :type: bool
    """

    use_bulge_min: bool
    """ Use lower limit for volume variation

    :type: bool
    """

    use_chain_offset: bool
    """ Offset the entire chain relative to the root joint

    :type: bool
    """

    use_curve_radius: bool
    """ Average radius of the endpoints is used to tweak the X and Z Scaling of the bones, on top of XZ Scale mode

    :type: bool
    """

    use_even_divisions: bool
    """ Ignore the relative lengths of the bones when fitting to the curve

    :type: bool
    """

    use_original_scale: bool
    """ Apply volume preservation over the original scaling

    :type: bool
    """

    xz_scale_mode: str
    """ Method used for determining the scaling of the X and Z axes of the bones

    :type: str
    """

    y_scale_mode: str
    """ Method used for determining the scaling of the Y axis of the bones, on top of the shape and scaling of the curve itself

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
